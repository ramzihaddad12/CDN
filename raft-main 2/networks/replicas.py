from typing import List, Dict, Any, Optional, Set, Union, Tuple

import socket
import json
import dataclasses

from datetime import datetime, timedelta

from abc import ABC, abstractmethod

from networks.message import deserialize_message, HelloMessage, Message

from networks.state_machine import TermState
from networks.constants import (
    DEFAULT_HOST,
    BROADCAST_DESTINATION,
    DEFAULT_BUFFER_BYTE_SIZE, DEFAULT_DATA_ENCODING
)


@dataclasses.dataclass(frozen=True)
class Replica(ABC):
    """
    Representation of a shared Replica State as defined in the 'Rules for Servers: All Servers' section of
    the Raft technical paper 
    """
    simulator_port: str
    this_id: str
    other_ids: Set[str]

    tcp_connection: socket.socket
    current_state: TermState

    term_logs: List[TermState]
    """save the committed term. This will be written whenever the state changes."""

    no_message_timeout: timedelta
    last_append_entries: datetime

    def send(self, message: Union[Message, List[Message]]) -> None:
        """
        Forward a json encoded message to the provided port
        """
        if isinstance(message, list):
            for sub_message in message:
                self._send(sub_message)
        else:
            self._send(message)

    def _send(self, message: Message) -> None:
        serialized_message = message.serialize_to_json()
        json_message = json.dumps(serialized_message)
        byte_message = json_message.encode(DEFAULT_DATA_ENCODING)
        self.tcp_connection.sendto(byte_message, (DEFAULT_HOST, self.simulator_port))

    def initialize_simulator(self) -> None:
        """
        Provide the simulator with data that it needs to launch properly
        """
        # NOTE: Hello message is essential for the simulator
        print(f"Replica {self.this_id} starting up", flush=True)
        hello_msg = HelloMessage(src=self.this_id, dst=BROADCAST_DESTINATION, leader=BROADCAST_DESTINATION)
        self.send(hello_msg)
        print(f"Sent hello message: {hello_msg.serialize_to_json()}", flush=True)

    def get_timeout(self) -> float:
        """
        :return: The amount of time that the replica should block (by default is the no_message_timeout)
        """
        return self.no_message_timeout.total_seconds()

    def handle_next_state(self) -> 'Replica':
        """
        Blocks until a timeout/message has been received, handles the event, and the returns the next state
        :return: Replica representing the next state of the program
        """
        second_timeout = self.get_timeout()
        # print(f"Timing out after {second_timeout} seconds")
        self.tcp_connection.settimeout(second_timeout)

        try:
            data, addr = self.tcp_connection.recvfrom(DEFAULT_BUFFER_BYTE_SIZE)
        except socket.timeout as te:
            # must have timedout after self.election_sec_timeout seconds
            timeout_response, timeout_next_state = self.handle_timeout()

            if timeout_response:
                self.send(timeout_response)

            return timeout_next_state

        str_msg = data.decode(DEFAULT_DATA_ENCODING)
        json_msg: Dict[str, Any] = json.loads(str_msg)

        message: Message = deserialize_message(json_msg)

        message_response, next_state = self.handle_message(parsed_message=message)
        if message_response:
            self.send(message_response)

        return next_state

    @abstractmethod
    def handle_message(self, parsed_message: Message) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: A response from the parsed message and update the current state accordingly
        """
        raise ValueError(f"Unknown message received {parsed_message}")

    @abstractmethod
    def handle_timeout(self) -> Tuple[Optional[Message], 'Replica']:
        """
        :return: A response message depending on the timeout message
        """
        ...
