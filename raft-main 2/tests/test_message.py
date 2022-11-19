import unittest

from networks.message import VoteRequest, deserialize_message


class TestDeserialize(unittest.TestCase):

    def test_deserialize_vote_request(self):
        raw_vote_request = {
            'src': '0001',
            'dst': 'FFFF',
            'leader': 'FFFF',
            'type': 'vote_request',
            'term': 1,
            'candidateId': '0001',
            'last_log_index': 3,
            'last_log_term': 0
        }

        vote_request = deserialize_message(raw_vote_request)
        expected_vote_request = VoteRequest(src='0001', dst='FFFF', leader='FFFF', term=1,
                                            candidateId='0001', last_log_index=3, last_log_term=0)

        self.assertEqual(expected_vote_request, vote_request)


if __name__ == '__main__':
    unittest.main()
