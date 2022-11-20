import unittest

import sys
import io
import socket

from unittest.mock import patch, Mock, call

from networks.message import MessageType
from networks.state_machine import CandidateTermState, TermState
from networks.replicas import Candidate, Follower
from networks.message import Message
from networks.constants import BROADCAST_DESTINATION, DEFAULT_FOLLOWER_HEARTBEAT_TIMEOUT, EPOCH_START_TIME, DEFAULT_DATA_ENCODING


class TestCandidateTimeout(unittest.TestCase):
  def test_candidate_timeout(self):
    candidate_term_state = CandidateTermState(
            term_count=1,
            log_entry=[],
            leader_id_vote=123,
            last_applied_log_count=0,
            last_commit_log_count=0,
            received_vote_ids=[123, 491]
        )

    candidate = Candidate(
        simulator_port="",
        this_id="",
        other_ids=[],
        tcp_connection=None,
        current_state=candidate_term_state,
        # no_message_timeout is guaranteed to have some value between 1.5 and 3.0
        no_message_timeout=1.5,
        last_heartbeat=EPOCH_START_TIME
    )

    _, new_candidate = candidate.handle_timeout()
    new_candidate: Candidate = new_candidate
    self.assertEqual(new_candidate.current_state.term_count, 2)
    self.assertEqual(len(new_candidate.current_state.received_vote_ids), 1)

if __name__ == '__main__':
    unittest.main()