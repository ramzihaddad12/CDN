from typing import List, Dict, Any, Optional, Set, Union, Tuple

import dataclasses

from datetime import datetime, timedelta

from networks.message import (
    AppendEntryRequest, AppendEntryResponse, FailMessage, GetRequest, MessageType,
    PutRequest, Message,
    VoteResponse, OkPutResponse, OkGetResponse, Entry
)

from networks.replicas import Replica
from networks.state_machine import LeaderTermState
from networks.constants import (
    BROADCAST_DESTINATION,
    DEFAULT_UNCOMMITTED_LOG_TIMEOUT,
    IMMEDIATE_TIMEOUT_VALUE,
    MAX_UNCOMMITTED_LOG_COUNT,
    MISSING_ENTRY_VALUE,
    DEFAULT_LEADER_HEARTBEAT_TIMEOUT
)


@dataclasses.dataclass(frozen=True)
class Leader(Replica):
    """
    Representation of a LEADER State as defined in the 'Rules for Servers: Leaders' section of
    the Raft technical paper  
    """
    current_state: LeaderTermState
    # override the current state typing
    append_entry_timeout: timedelta

    entries: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def get_timeout(self) -> float:
        """
        :return: The uncommitted message timeout if necessary, otherwise the 
        """
        # print(f"Entered function and have {self.no_message_timeout} or hb {self.append_entry_timeout}")
        if not self.current_state.uncommitted_entries:
            accepted_timeout = self.append_entry_timeout
        elif len(self.current_state.uncommitted_entries) + 1 >= MAX_UNCOMMITTED_LOG_COUNT:
            accepted_timeout = IMMEDIATE_TIMEOUT_VALUE
        else:
            accepted_timeout = DEFAULT_UNCOMMITTED_LOG_TIMEOUT

        expected_endtime = self.last_append_entries + accepted_timeout
        time_until_expected = expected_endtime - datetime.now()

        filtered_timeout = max(time_until_expected, IMMEDIATE_TIMEOUT_VALUE)
        # print(f"Need to timeout in {filtered_timeout.total_seconds()} seconds")
        return filtered_timeout.total_seconds()

    def handle_timeout(self) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: A heartbeat informing all other replicas that this leader is still alive
        """
        calculated_timeout = datetime.now() - self.last_append_entries
        print(f"Timed out after {calculated_timeout.total_seconds()} seconds at LEADER", flush=True)

        # whenever there is a timeout, need to send off all of the uncommitted entries
        #   if there are NO uncommitted entries, this will just send off an empty list
        append_entries_request = AppendEntryRequest(
            src=self.this_id,
            dst=BROADCAST_DESTINATION,
            leader=self.this_id,
            term=self.current_state.term_count,
            last_log_index=0,
            last_log_term=0,
            entries=self.current_state.uncommitted_entries,
            leader_commit_index=0
        )
        # print(f"Sending uncommitted entries: {self.current_state.uncommitted_entries}", flush=True)

        # assume that the uncommitted entries are going to be taken care of
        #   can revert back to the leader append_entry timeout
        full_entries = self.current_state.log_entries + self.current_state.uncommitted_entries

        next_term_state = dataclasses.replace(self.current_state, uncommitted_entries=[], log_entries=full_entries)

        next_leader = dataclasses.replace(
            self, append_entry_timeout=DEFAULT_LEADER_HEARTBEAT_TIMEOUT,
            current_state=next_term_state, last_append_entries=datetime.now())

        return append_entries_request, next_leader

    def handle_message(self, parsed_message: Message) -> Tuple[Optional[Message], 'Replica']:
        """
        Base handle for all messages received by this replica
        """
        # the RETURNED messages from the leader need to have an appropriately calculated timeout for the heartbeat
        if parsed_message.type == MessageType.GET:
            return self.handle_get_request(get_request=parsed_message)

        if parsed_message.type == MessageType.PUT:
            return self.handle_put_request(put_request=parsed_message)

        if parsed_message.type == MessageType.VOTE_RESPONSE:
            return self.handle_vote_response(vote_response=parsed_message)

        if parsed_message.type == MessageType.APPEND_RESPONSE:
            return self.handle_append_entry_response(append_entry_response=parsed_message)

        return super().handle_message(parsed_message=parsed_message)

    def handle_get_request(self, get_request: GetRequest) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: A redirect if we are not the leader, and an appropriate ok/fail if we are
        """
        # if the entry is committed, get the value
        retrieved_value = self.entries.get(get_request.key, MISSING_ENTRY_VALUE)

        if retrieved_value == MISSING_ENTRY_VALUE:
            response_message = FailMessage(
                src=self.this_id,
                dst=get_request.src,
                leader=self.this_id,
                MID=get_request.MID)
        else:
            response_message = OkGetResponse(
                src=self.this_id,
                dst=get_request.src,
                leader=self.this_id,
                MID=get_request.MID,
                value=retrieved_value)

        return response_message, self

    def handle_put_request(self, put_request: PutRequest) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: A redirect if we are not the leader, an an appropriate ok/fail if we are
        """
        # ADD TO THE RUNNING LIST
        updated_local_entries = dict(self.entries)
        updated_local_entries[put_request.key] = put_request.value

        updated_log_entries = self.current_state.uncommitted_entries + [Entry(term=self.current_state.term_count,
                                                                              key=put_request.key, value=put_request.value)]

        updated_leader_state = dataclasses.replace(self.current_state, uncommitted_entries=updated_log_entries)

        next_leader = dataclasses.replace(self, current_state=updated_leader_state, entries=updated_local_entries)

        # ONLY send the OK message once the entries have been approved by the other replicas
        fail_message = OkPutResponse(
            src=self.this_id,
            dst=put_request.src,
            leader=self.this_id,
            MID=put_request.MID)

        return fail_message, next_leader

    def handle_vote_response(self, vote_response: VoteResponse) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: Add an approved vote to the list of received votes
        """
        if vote_response.vote_granted:
            # update the saved votes if this is the leader
            updated_votes = self.current_state.recieved_vote_ids | {vote_response.src}
            updated_term_state = dataclasses.replace(self.current_state, recieved_vote_ids=updated_votes)
            updated_vote_leader_state = dataclasses.replace(self, current_state=updated_term_state)
            return None, updated_vote_leader_state

        return None, self

    def handle_append_entry_response(self, append_entry_response: AppendEntryResponse) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: Inform a client that a put request is approved
        """
        # if the response has a log_index that matches the newest
        #   don't need to do anything

        # if the response has a log_index that is LOWER than the newest
        #   need to send it the first X values (this should repeat from more responses until the replica is up to date)

        # update the highest saved log_index for that replica ID

        return None, self
