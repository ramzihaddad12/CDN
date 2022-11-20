from typing import List, Dict, Any, Optional, Set, Union, Tuple

import dataclasses
from networks.leader import Leader

from networks.message import (
    AppendEntryRequest, AppendEntryResponse, ClientMessage, Entry, MessageType,
    RedirectResponse, VoteRequest, Message,
    VoteResponse
)

from networks.replicas import Replica
from networks.state_machine import CandidateTermState, LeaderTermState, TermState
from networks.constants import (
    BROADCAST_DESTINATION,
    EPOCH_START_TIME,
    DEFAULT_LEADER_HEARTBEAT_TIMEOUT
)


@dataclasses.dataclass(frozen=True)
class NonLeader(Replica):
    """
    Representation of a Replica that does NOT lead
    """

    def handle_redirect(self, request_message: ClientMessage) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: A message that redirects the requester to the current leader
        """
        if self.current_state.leader_id_vote:
            # print(f"Redirecting message {request_message} to {self.current_state.leader_id_vote}")
            redirect_response = RedirectResponse(
                src=self.this_id,
                dst=request_message.src,
                leader=self.current_state.leader_id_vote,
                MID=request_message.MID
            )
            return redirect_response, self

        raise RuntimeError(f"Unknown state entered where a leader has not been elected")

    def handle_message(self, parsed_message: Message) -> Tuple[Optional[Message], 'Replica']:
        """
        A CANDIDATE needs to handle:
        """
        if parsed_message.type == MessageType.GET:
            return self.handle_redirect(request_message=parsed_message)

        if parsed_message.type == MessageType.PUT:
            return self.handle_redirect(request_message=parsed_message)

        return super().handle_message(parsed_message)


@dataclasses.dataclass(frozen=True)
class Candidate(NonLeader):
    """
    Representation of a CANDIDATE State as defined in the 'Rules for Servers: Candidates' section of
    the Raft technical paper  
    """
    current_state: CandidateTermState
    # override the current state typing

    def generate_vote_request(self) -> VoteRequest:
        """
        :return: Generate a request for a Vote with a term 1 higher than the follower currently has
        """
        return VoteRequest(
            src=self.this_id,
            dst=BROADCAST_DESTINATION,
            leader=BROADCAST_DESTINATION,
            term=self.current_state.term_count,
            candidateId=self.this_id,
            last_log_index=0,
            last_log_term=0
        )

    def handle_timeout(self) -> Tuple[Optional[Message], 'Replica']:
        """
        If a Candidate times out, it needs to start an election process by incrementing
        the term and initiating another round of RequestVote RPCs
        """

        print(f"Timed out after {self.no_message_timeout.total_seconds()} seconds at CANDIDATE")

        # Incrementing the term count and resetting the received_vote_ids to just you. Everything else stays the same.
        updated_current_state = dataclasses.replace(
            self.current_state,
            term_count=self.current_state.term_count + 1,
            received_vote_ids=[self.this_id]
        )

        updated_state = dataclasses.replace(self, current_state=updated_current_state)

        vote_request = updated_state.generate_vote_request()
        return vote_request, updated_state

    def handle_message(self, parsed_message: Message) -> Tuple[Optional[Message], 'Replica']:
        """
        Base handler for all messages received by the replica
        """
        if parsed_message.type == MessageType.VOTE_RESPONSE:
            return self.handle_vote_response(vote_response=parsed_message)

        if parsed_message.type == MessageType.VOTE_REQUEST:
            return self.handle_vote_request(vote_request=parsed_message)

        if parsed_message.type == MessageType.APPEND_REQUEST:
            return self.handle_append_entry(append_request=parsed_message)

        return super().handle_message(parsed_message=parsed_message)

    def handle_vote_request(self, vote_request: VoteRequest) -> Tuple[Optional[Message], 'Replica']:
        """
        Determine whether heartbeat and response accordingly
        """
        # if you get a heartbeat, make sure that the term is within range
        if vote_request.term < self.current_state.term_count:
            # we are the better candidate, so we reject the RPC from the other replica
            # and continue to exist in the candidate state.
            return None, self

        if vote_request.last_log_index < self.current_state.last_commit_log_count:
            # we are the better candidate, so we reject the RPC from the other replica
            # and continue to exist in the candidate state.
            return None, self

        if (vote_request.term == self.current_state.term_count and
                self.current_state.last_commit_log_count == vote_request.last_log_index):
            # don't make sense to vote for the other RPC
            return None, self

        return None, self

    def handle_vote_response(self, vote_response: VoteResponse) -> Tuple[Optional[Message], 'Replica']:
        """
        Handle the case where the replica recieves a vote response
        """
        if not vote_response.vote_granted:
            return None, self

        # If the vote HAS been granted
        new_received_votes = self.current_state.received_vote_ids | {vote_response.src}

        if len(new_received_votes) > int(len(self.other_ids) / 2):
            # if the majority vote was received
            # increment the term_count and initialize the term tracking variables
            leader_term_state = LeaderTermState(
                term_count=self.current_state.term_count,
                uncommitted_entries=self.current_state.uncommitted_entries,
                log_entries=self.current_state.log_entries,
                leader_id_vote=self.current_state.leader_id_vote,
                recieved_vote_ids=self.current_state.received_vote_ids,
                received_put_responses=dict())

            next_leader_state = Leader(
                simulator_port=self.simulator_port,
                this_id=self.this_id,
                term_logs=self.term_logs,
                other_ids=self.other_ids,
                tcp_connection=self.tcp_connection,
                current_state=leader_term_state,
                append_entry_timeout=DEFAULT_LEADER_HEARTBEAT_TIMEOUT,
                no_message_timeout=self.no_message_timeout,
                last_append_entries=EPOCH_START_TIME)

            # print(f"Creating a LEADER with election {repr(next_leader_state.no_message_timeout)} and "
            #       f"normal {repr(next_leader_state.append_entry_timeout)}")

            print(f"THIS WAS ELECTED LEADER")
            return None, next_leader_state

        # if the majority was NOT received
        new_term_state: CandidateTermState = dataclasses.replace(self.current_state,
                                                                 received_vote_ids=new_received_votes)

        next_candidate_state: Candidate = dataclasses.replace(self, current_state=new_term_state)
        return None, next_candidate_state

    def handle_append_entry(self, append_request: AppendEntryRequest) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: A follower
        """
        # if you get a heartbeat, make sure that the term is within range
        if append_request.term < self.current_state.term_count:
            # we are the better candidate, so we reject the RPC from the other replica
            # and continue to exist in the candidate state.
            return None, self

        if append_request.last_log_index < self.current_state.last_commit_log_count:
            # we are the better candidate, so we reject the RPC from the other replica
            # and continue to exist in the candidate state.
            return None, self

        if (append_request.term == self.current_state.term_count and
                self.current_state.last_commit_log_count == append_request.last_log_index):
            # don't make sense to vote for the other RPC
            return None, self

        # we need to revert back to a follower
        follower_state = TermState(
            term_count=self.current_state.term_count,
            uncommitted_entries=self.current_state.uncommitted_entries,
            log_entries=self.current_state.log_entries,
            leader_id_vote=None)  # leader will be handled by the vote_request of the follower

        follower_replica = Follower(
            simulator_port=self.simulator_port,
            this_id=self.this_id,
            other_ids=self.other_ids,
            tcp_connection=self.tcp_connection,
            current_state=follower_state,
            term_logs=self.term_logs,
            no_message_timeout=self.no_message_timeout,
            last_append_entries=self.last_append_entries)

        vote_response = follower_replica.handle_append_request(append_request=append_request)
        return vote_response, follower_replica


class Follower(NonLeader):
    """
    Representation of a FOLLOWER State as defined in the 'Rules for Servers: Followers' section of
    the Raft technical paper  
    """

    def handle_message(self, parsed_message: Message) -> Tuple[Optional[Message], 'Replica']:
        """
        Base handler for the message received by the Replica
        """
        if parsed_message.type == MessageType.VOTE_REQUEST:
            return self.handle_vote_request(vote_request=parsed_message)

        if parsed_message.type == MessageType.APPEND_REQUEST:
            return self.handle_append_request(append_request=parsed_message)

        return super().handle_message(parsed_message)

    def handle_timeout(self) -> Tuple[Optional[Message], 'Replica']:
        """
        If a Follower times out, it needs to start an election process
        """
        # need to return a candidate
        print(f"Timed out after {self.no_message_timeout.seconds} seconds at FOLLOWER")

        # make sure it's saved that we voted for ourselves
        next_candidate_term_state = CandidateTermState(
            term_count=self.current_state.term_count + 1,
            log_entries=self.current_state.log_entries,
            uncommitted_entries=self.current_state.uncommitted_entries,
            leader_id_vote=self.this_id,
            received_vote_ids={self.this_id}
        )
        next_candidate = Candidate(
            simulator_port=self.simulator_port,
            this_id=self.this_id,
            other_ids=self.other_ids,
            tcp_connection=self.tcp_connection,
            current_state=next_candidate_term_state,
            no_message_timeout=self.no_message_timeout,
            last_append_entries=self.last_append_entries,
            term_logs=self.term_logs
        )

        vote_request = next_candidate.generate_vote_request()
        return vote_request, next_candidate

    def handle_vote_request(self, vote_request: VoteRequest) -> Optional[Message]:
        """
        :return: A request with True or False depending on whether a candidate is accepted
        """
        grant_vote = True

        # reply false if the provided term is less than the current term
        if vote_request.term < self.current_state.term_count:
            grant_vote = False

        if self.current_state.leader_id_vote is not None:
            # don't do anything if you've already voted
            return None, self

        new_term_state = dataclasses.replace(self.current_state, leader_id_vote=vote_request.candidateId)
        new_replica_state = dataclasses.replace(self, current_state=new_term_state)

        vote_response = VoteResponse(
            src=self.this_id,
            dst=vote_request.src,
            leader=BROADCAST_DESTINATION,
            term=self.current_state.term_count,
            vote_granted=grant_vote
        )

        return vote_response, new_replica_state

    def _generate_entry_response(self, append_request: AppendEntryRequest) -> AppendEntryResponse:
        """
        :return: A refusal for a provided append_entries request
        """
        replica_refusal_response = AppendEntryResponse(src=self.this_id, dst=append_request.src,
                                                       leader=self.current_state.leader_id_vote,
                                                       term=self.current_state.term_count,
                                                       last_log_index=self.current_state.last_commit_log_count,
                                                       last_log_term=self.current_state.term_count)
        return replica_refusal_response

    def handle_append_request(self, append_request: AppendEntryRequest) -> Optional[Message]:
        """
        :return: Confirmation of the append request
        """
        # The sender of the append request is now our leader if we did not have one already
        if self.current_state.leader_id_vote != append_request.leader:
            # FIXME: Actually add logic here to handle the heartbeat
            new_term_state = dataclasses.replace(self.current_state, leader_id_vote=append_request.leader)
            new_replica = dataclasses.replace(self, current_state=new_term_state)
            print(f"Set current leader to {new_term_state.leader_id_vote}", flush=True)
            return None, self

        # "if the follower does not find an entry in its log with the same index and term, it refuses the new entries"
        replica_refusal_response = self._generate_entry_response(append_request=append_request)

        if self.current_state.last_commit_log_count != append_request.last_log_index:
            return replica_refusal_response, self

        # if there are no replicas committed yet
        if self.current_state.last_commit_log_count == 0:
            # the logs must be applied during the term that the replica is currently in
            if self.current_state.term_count != append_request.last_log_term:
                return replica_refusal_response, self

            # add these to the logs that are queued but so-far uncommitted
            updated_uncommitted_logs = append_request.entries

            confirmation_response = self._generate_entry_response(append_request=append_request)
            updated_term_state = dataclasses.replace(self.current_state, uncommitted_entries=updated_uncommitted_logs)
            updated_replica = dataclasses.replace(self, current_state=updated_term_state)
            return confirmation_response, updated_replica

        # this replica has a log that might need to be committed
        matched_log = self.current_state.log_entries[self.current_state.last_applied_log_index]

        return self._handle_matched_log_response(append_request=append_request, matched_log=matched_log)

    def _handle_matched_log_response(self, append_request: AppendEntryRequest, matched_log: Entry) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: A response based on a found log
        """
        log_refusal_response = self._generate_entry_response(append_request=append_request)

        if matched_log.term != append_request.last_log_term:
            return log_refusal_response, self

        if matched_log.term < self.current_state.term_count:
            # raise NotImplementedError(f"Unsure of what to do when the log term {matched_log.term}"
            #                           f" is less than the current state {self.current_state.term_count}")
            # make sure that the
            return log_refusal_response, self

        # this replica CAN commit messages up to what the leader has committed
        num_commitable_entries = append_request.leader_commit_index - self.current_state.last_applied_log_count
        commitable_entries = self.current_state.uncommitted_entries[:num_commitable_entries]

        updated_committed_entries = self.current_state.log_entries + commitable_entries
        remaining_uncommitted_entries = self.current_state.uncommitted_entries[num_commitable_entries:]

        updated_state = dataclasses.replace(self.current_state,
                                            log_entries=updated_committed_entries,
                                            uncommitted_entries=remaining_uncommitted_entries)

        updated_replica = dataclasses.replace(self, current_state=updated_state)

        last_entry = updated_state.log_entries[updated_state.last_commit_log_count]

        # return that the associated entries have been committed
        log_accepted_response = AppendEntryResponse(src=self.this_id, dst=append_request.src,
                                                    leader=self.current_state.leader_id_vote,
                                                    term=self.current_state.term_count,
                                                    last_log_index=updated_state.last_commit_log_count,
                                                    last_log_term=last_entry.term)

        return log_accepted_response, updated_replica
