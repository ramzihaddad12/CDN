from typing import Tuple
from datetime import datetime, timedelta

BROADCAST_DESTINATION: str = 'FFFF'
"""
Destination string indicating that the message should be broadcast to all LAN sockets
"""


MESSAGE_TYPE_VAR_NAME: str = 'type'
"""
Name for the message type
"""


DEFAULT_HOST: str = 'localhost'
"""
Default socket host value
"""


ANY_SOURCE_BIND_ADDRESS: Tuple[str, int] = (DEFAULT_HOST, 0)
"""
Socket address indicating that any local socket connection will be accepted
"""


DEFAULT_BUFFER_BYTE_SIZE: int = 65535
"""
Default value for the size of a receive buffer
"""


DEFAULT_DATA_ENCODING: str = 'utf-8'
"""
Default encoding/decoding value from string to bytes
"""


DEBUG_TIMEOUT_MULTIPLIER: float = 10.0
"""
Used to slow down the workings
"""


DEFAULT_LEADER_HEARTBEAT_TIMEOUT: timedelta = timedelta(seconds=.07 * DEBUG_TIMEOUT_MULTIPLIER)
"""
Default amount of time gone by before leader sends another heartbeat.

Note: it's necessary to have this value lie underneath 150-300ms (election timeout)
so that another election isn't unnecessarily begun
"""


DEFAULT_UNCOMMITTED_LOG_TIMEOUT: timedelta = timedelta(seconds=0.015 * DEBUG_TIMEOUT_MULTIPLIER)
"""
Default amount of time before a batch of uncommitted logs are sent off
"""


MAX_UNCOMMITTED_LOG_COUNT: int = 5
"""
The maximum number of uncommitted logs before a Leader sends off batched requests
"""


IMMEDIATE_TIMEOUT_VALUE: timedelta = timedelta(microseconds=100)
"""
Value to set the socket timeout to which causes an "immediate" timeout

According to the socket man page:
    The value argument can be a nonnegative floating point number expressing seconds, or None. 
    If a non-zero value is given, subsequent socket operations will raise a timeout exception if the timeout period value 
    has elapsed before the operation has completed. 
    If zero is given, the socket is put in non-blocking mode. If None is given, the socket is put in blocking mode.
"""


EPOCH_START_TIME: datetime = datetime.fromordinal(1)
"""
Time representation of the EPOCH
"""


SEC_TO_MICRO_SEC_DIV: float = 1000000.0
"""
Conversion from seconds to microseconds
"""


MISSING_ENTRY_VALUE: str = ""
"""
Value to be returned if an entry is not found within the data store
"""


class RangeConstants:
    START: int = 150
    STOP: int = 300
    STEP: int = 5

    DIVISOR: float = 1000.0 / DEBUG_TIMEOUT_MULTIPLIER


class CommandLineConstants:
    PORT_VAR_NAME: str = "port"
    """
    Value of the required PORT argument
    """

    ID_VAR_NAME: str = "id"
    """
    Name of the required ID argument
    """

    OTHER_REPLICA_IDS_VAR_NAME: str = "others"
    """
    Name of the variable containing the other replica ID's
    """
