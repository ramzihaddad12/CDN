import unittest

import sys
import io
import socket

from unittest.mock import patch, Mock, call

from networks.message import HelloMessage, MessageType
from networks.state_machine import TermState
from networks.replicas import Follower
from networks.message import Message
from networks.constants import BROADCAST_DESTINATION, EPOCH_START_TIME, DEFAULT_DATA_ENCODING, RangeConstants as RC


class TestFollowerInstantiation(unittest.TestCase):

    @patch('sys.stdout')
    def test_follower_construction(self, _mocked_stdout: Mock):
        # every replica starts as a follower
        starter_state = TermState(term_count=0,
                                  uncommitted_entries=[],
                                  log_entries=[],
                                  leader_id_vote=None,
                                  last_applied_log_count=0,
                                  last_commit_log_count=0)

        election_timeout = RC.START / RC.DIVISOR

        replica = Follower(simulator_port=10,
                           this_id="yolo",
                           other_ids=["world", "friend"],
                           tcp_connection=None,
                           current_state=starter_state,
                           no_message_timeout=election_timeout,
                           term_logs=[],
                           last_append_entries=EPOCH_START_TIME)

        with patch('networks.replicas.Follower.send', new_callable=Mock) as mocked_send:
            mocked_send: Mock = mocked_send
            replica.initialize_simulator()

        expected_message = HelloMessage(src='yolo', dst=BROADCAST_DESTINATION,
                                        leader=BROADCAST_DESTINATION)
        expected_call = call(expected_message)
        self.assertEqual([expected_call], mocked_send.mock_calls)


if __name__ == '__main__':
    unittest.main()
