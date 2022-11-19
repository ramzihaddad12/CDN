from typing import Type, Dict, Any, List

import dataclasses

from enum import Enum


from networks.constants import MESSAGE_TYPE_VAR_NAME


class MessageType(str, Enum):
    UNKNOWN = 'parent'
    HELLO = 'hello'
    GET = 'get'
    PUT = 'put'
    OK = 'ok'
    FAIL = 'fail'
    REDIRECT = 'redirect'
    VOTE_REQUEST = 'vote_request'
    VOTE_RESPONSE = 'vote_response'
    APPEND_REQUEST = 'append_request'
    APPEND_RESPONSE = 'append_response'

    def __str__(self) -> str:
        return self.value


@dataclasses.dataclass(frozen=True)
class JsonSerializable:
    @classmethod
    def deserialize_from_json(cls, class_object: Dict[str, Any]) -> 'JsonSerializable':
        """
        :return: An instance of this class provided the fields
        """
        parsed_key_word_arguments: Dict[str, Any] = {}

        for dataclass_field in dataclasses.fields(cls):
            if not dataclass_field.init:
                continue
            field_constructor = dataclass_field.type
            field_name = dataclass_field.name

            raw_field_value = class_object.get(field_name)
            field_value = cls.convert_raw_to_final(raw_value=raw_field_value, field_type=field_constructor)

            parsed_key_word_arguments[field_name] = field_value

        return cls(**parsed_key_word_arguments)

    @classmethod
    def convert_raw_to_final(cls, raw_value: Any, field_type: Type) -> Any:
        """
        Provided a field type, convert to the final value
        """
        return field_type(raw_value)

    def serialize_to_json(self) -> Dict[str, Any]:
        """
        :return: A json object from the current instance
        """
        serialized_dict: Dict[str, Any] = {}

        for dataclass_field in dataclasses.fields(self):
            field_name = dataclass_field.name
            raw_field_value = getattr(self, field_name)

            serialized_dict[field_name] = self.serialize_raw_to_final(
                raw_value=raw_field_value, field_type=dataclass_field.type)

        return serialized_dict

    def serialize_raw_to_final(self, raw_value: Any, field_type: Type) -> Any:
        """
        :return: A json string from the current field
        """
        return str(raw_value)


@dataclasses.dataclass(frozen=True)
class Message(JsonSerializable):
    src: str
    dst: str
    leader: str
    type: MessageType = dataclasses.field(init=False, default=None)
    """THIS IS OVERRIDEN IN THE CHILD CLASSES"""


@dataclasses.dataclass(frozen=True)
class HelloMessage(Message):
    type: MessageType = dataclasses.field(init=False, default=MessageType.HELLO)


@dataclasses.dataclass(frozen=True)
class VoteRequest(Message):
    type: MessageType = dataclasses.field(init=False, default=MessageType.VOTE_REQUEST)
    term: int
    candidateId: str
    last_log_index: int
    last_log_term: int


@dataclasses.dataclass(frozen=True)
class VoteResponse(Message):
    type: MessageType = dataclasses.field(init=False, default=MessageType.VOTE_RESPONSE)
    term: int
    vote_granted: bool


@dataclasses.dataclass(frozen=True)
class Entry(JsonSerializable):
    term: int
    key: str
    value: str


@dataclasses.dataclass(frozen=True)
class AppendEntryRequest(Message):
    type: MessageType = dataclasses.field(init=False, default=MessageType.APPEND_REQUEST)
    term: int
    last_log_index: int
    last_log_term: int
    entries: List[Entry]
    leader_commit_index: int

    @classmethod
    def convert_raw_to_final(cls, raw_value: Any, field_type: Type) -> Any:
        if field_type == List[Entry]:
            raw_list = list(raw_value)
            return [Entry.deserialize_from_json(raw_entry) for raw_entry in raw_list]

        return super().convert_raw_to_final(raw_value=raw_value, field_type=field_type)

    def serialize_raw_to_final(self, raw_value: Any, field_type: Type) -> Any:
        """
        :return: A json string from the current field
        """
        if field_type == List[Entry]:
            # print(f"FOUND RAW VALUE: {raw_value}")
            return [entry_value.serialize_to_json() for entry_value in raw_value]

        return super().serialize_raw_to_final(raw_value=raw_value, field_type=field_type)


@dataclasses.dataclass(frozen=True)
class AppendEntryResponse(Message):
    type: MessageType = dataclasses.field(init=False, default=MessageType.APPEND_RESPONSE)
    term: int
    last_log_index: int
    """
    True if follower contained entry matching prev_log_index and prev_log_term
    """
    last_log_term: int


@dataclasses.dataclass(frozen=True)
class ClientMessage(Message):
    MID: str


@dataclasses.dataclass(frozen=True)
class FailMessage(ClientMessage):
    type: MessageType = dataclasses.field(init=False, default=MessageType.FAIL)


@dataclasses.dataclass(frozen=True)
class GetRequest(ClientMessage):
    type: MessageType = dataclasses.field(init=False, default=MessageType.GET)
    key: str


@dataclasses.dataclass(frozen=True)
class RedirectResponse(ClientMessage):
    type: MessageType = dataclasses.field(init=False, default=MessageType.REDIRECT)


@dataclasses.dataclass(frozen=True)
class PutRequest(ClientMessage):
    type: MessageType = dataclasses.field(init=False, default=MessageType.PUT)
    key: str
    value: str


@dataclasses.dataclass(frozen=True)
class OkPutResponse(ClientMessage):
    type: MessageType = dataclasses.field(init=False, default=MessageType.OK)


@dataclasses.dataclass(frozen=True)
class OkGetResponse(ClientMessage):
    type: MessageType = dataclasses.field(init=False, default=MessageType.OK)
    value: str


def deserialize_message(json_message_object: Dict[str, Any]) -> Message:
    """
    :return: The specific message for a given type
    """
    raw_message_type = json_message_object.pop(MESSAGE_TYPE_VAR_NAME)
    message_type = MessageType(raw_message_type)

    if message_type == MessageType.VOTE_REQUEST:
        return VoteRequest.deserialize_from_json(json_message_object)

    elif message_type == MessageType.VOTE_RESPONSE:
        return VoteResponse.deserialize_from_json(json_message_object)

    elif message_type == MessageType.APPEND_REQUEST:
        return AppendEntryRequest.deserialize_from_json(json_message_object)

    elif message_type == MessageType.APPEND_RESPONSE:
        return AppendEntryResponse.deserialize_from_json(json_message_object)

    elif message_type == MessageType.GET:
        return GetRequest.deserialize_from_json(json_message_object)

    elif message_type == MessageType.REDIRECT:
        return RedirectResponse.deserialize_from_json(json_message_object)

    elif message_type == MessageType.PUT:
        return PutRequest.deserialize_from_json(json_message_object)

    raise ValueError(f"Unknown message type {message_type} for message {json_message_object}")
