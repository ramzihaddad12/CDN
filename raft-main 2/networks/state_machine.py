from typing import List, Optional, Set, Dict

from dataclasses import dataclass

from networks.message import Entry


@dataclass(frozen=True)
class TermState:
    term_count: int

    uncommitted_entries: List[Entry]
    """entries that have been received but have not been committed to the actual replica"""
    log_entries: List[Entry]
    """entries that have been committed"""
    leader_id_vote: Optional[str]
    """id of the leader that was voted for in this term"""

    @property
    def last_applied_log_count(self) -> int:
        """index of the highest log entry applied to state machine. Initialized to 0. First log is at index 1"""
        return len(self.log_entries) + len(self.uncommitted_entries)

    @property
    def last_commit_log_count(self) -> int:
        """index of the highest log entry known to be committed. Initialized to 0. First log is at index 1"""
        return len(self.log_entries)

    @property
    def last_applied_log_index(self) -> Optional[int]:
        return None if self.last_applied_log_count == 0 else self.last_applied_log_count - 1

    @property
    def last_commit_log_index(self) -> Optional[int]:
        return None if self.last_commit_log_count == 0 else self.last_commit_log_count - 1


@dataclass(frozen=True)
class CandidateTermState(TermState):
    received_vote_ids: Set[str]
    """ids of the votes that this leader has received"""


@dataclass(frozen=True)
class LeaderTermState(TermState):
    recieved_vote_ids: Set[str]
    """ids of the votes that this leader has received"""

    received_put_responses: Dict[int, Set[str]]
    """ids of the voters that approved a put message for a provided term number"""

    @property
    def next_log_index(self) -> int:
        """index of the next log entry to send to a server. Initialize to last_applied_log_index + 1"""
        return self.last_applied_log_index + 1
