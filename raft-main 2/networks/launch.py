from typing import List

import argparse
import socket
import random

from datetime import timedelta

from networks.non_leader import Follower
from networks.state_machine import TermState
from networks.constants import (
    CommandLineConstants as CLC,
    RangeConstants as RC,
    ANY_SOURCE_BIND_ADDRESS, EPOCH_START_TIME
)


def create_parser() -> argparse.ArgumentParser:
    """
    :return: Argument parser for the Key-Value Consensus Data Store
    """
    parser = argparse.ArgumentParser(description='run a key-value store')
    parser.add_argument(CLC.PORT_VAR_NAME, type=int, help="Port number to communicate")
    parser.add_argument(CLC.ID_VAR_NAME, type=str, help="ID of this replica")
    parser.add_argument(CLC.OTHER_REPLICA_IDS_VAR_NAME,
                        metavar=CLC.OTHER_REPLICA_IDS_VAR_NAME,
                        type=str, nargs='+', help="IDs of other replicas")

    return parser


def launch_replica(destination_port: str, replica_id: str, other_replica_ids: List[str]) -> None:
    """
    Instantiate the replica
    """
    raw_election_timeout: float = random.randrange(RC.START, RC.STOP, RC.STEP) / RC.DIVISOR
    election_timeout = timedelta(seconds=raw_election_timeout)
    print(f"Initialized with election timeout: {election_timeout.total_seconds()}")
    others_set = set(other_replica_ids)

    # if the socket closes, need to re-instantiate a Replica anyways
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as tcp_socket:
        tcp_socket.bind(ANY_SOURCE_BIND_ADDRESS)

        # every replica starts as a follower
        starter_state = TermState(term_count=0,
                                  uncommitted_entries=[],
                                  log_entries=[],
                                  leader_id_vote=None)

        replica = Follower(simulator_port=destination_port,
                           this_id=replica_id,
                           other_ids=others_set,
                           tcp_connection=tcp_socket,
                           current_state=starter_state,
                           no_message_timeout=election_timeout,
                           term_logs=[],
                           last_append_entries=EPOCH_START_TIME)

        # ONLY happens the FIRST time the replica is launched
        replica.initialize_simulator()

        while replica:
            # actually handle the message
            #   NOTE: By designing this way. It's possible to instantiate a Replica in the Tests in a given state
            #   THEN, one can test how that specific state responds to input
            #   ... Allows for very deterministic testing
            #   ... Can also save the next state in logs somewhere depending on how creative we get here
            replica = replica.handle_next_state()


if __name__ == '__main__':
    kv_parser = create_parser()

    kv_args = kv_parser.parse_args()

    input_port: str = getattr(kv_args, CLC.PORT_VAR_NAME)
    input_replica_id: str = getattr(kv_args, CLC.ID_VAR_NAME)
    input_other_replica_ids: List[str] = getattr(kv_args, CLC.OTHER_REPLICA_IDS_VAR_NAME)

    launch_replica(destination_port=input_port,
                   replica_id=input_replica_id,
                   other_replica_ids=input_other_replica_ids)
