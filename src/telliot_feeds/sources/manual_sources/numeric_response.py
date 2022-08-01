from ast import literal_eval
from dataclasses import dataclass
from decimal import Decimal
from collections import deque
from telliot_feeds.datasource import DataSource
from typing import Any, List, Tuple
from telliot_feeds.queries.abi_query import AbiQuery
from eth_abi import encode_single
from telliot_core.utils.response import ResponseStatus, error_status
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger

logger = get_logger(__name__)

status = ResponseStatus()


def is_length_greater_than_one(abi_type: List[str]) -> bool:
    """Checks the length of the value type reponse items that needs to deciphered"""
    if len(abi_type) > 1:
        return True
    return False


def is_list(abi_type: str) -> bool:
    bracket = '[]'
    if abi_type[-2:] == bracket or abi_type[-3:-1] == bracket:
        return True
    return False


def _validate_user_input_single_item(_abi_type: str, _user_input: Any) -> Tuple[Any, Any]:
    if _abi_type[0] == '(' and _abi_type[-1] == ')':
        try:
            _usr_input = [tuple(map(Decimal, literal_eval(_user_input)))]
            return _usr_input, status
        except ValueError as e:
            return None, error_status(note="Tuple items must be all decimals", e=e, log=logger.error)
    else:
        try:

            _user_input = literal_eval(_user_input)
            if type(_user_input) != tuple:
                _user_input = [_user_input]
            _user_input = list(map(Decimal, _user_input))
            return _user_input, status
        except ValueError as e:
            return None, error_status(note="All items must be deciamls", log=logger.error, e=e)


def _strip_single_item_input(_user_input: str) -> str:
    pare_brack = ['[', '(', ')', ']']
    if _user_input[0] in pare_brack and _user_input[-1] in pare_brack:
        return _user_input.strip(f'{_user_input[0]}{_user_input[-1]}')
    return _user_input


def _decimal_conversion(_user_input: str) -> Any:
    """Converts to Decimal in the instance that para"""
    pare_brack = ['[', '(', ')', ']']
    if _user_input[0] in pare_brack and _user_input[-1] in pare_brack:
        inpt = _user_input.strip(f'{_user_input[0]}{_user_input[-1]}')
        return [Decimal(inpt)]
    return Decimal(_user_input)


@dataclass
class ManualSource(DataSource[Any]):
    """
    Source for Maunual Numerical Oracle Response types
    example: ufixed256x18, ufixed256x18, fixed256x18
    (ufixed256x8,ufixed256x6), ufixed256x18[] etc.

    """

    def __init__(self, query: AbiQuery):
        self.query = query
        return super().__init__(DataSource)

    def __post_init__(self) -> None:
        # Overwrite default deque
        self._history = deque(maxlen=256)

    def get_abi_type(self) -> str:
        """Get query response abi type"""
        return self.query.value_type.abi_type

    def encode(self, value: str) -> bytes:
        """Get value encoder"""
        return self.query.value_type.encode(value)

    def user_input(self) -> str:
        """Get user input"""
        # example input
        # maybe should display the abi type here as a hint or example
        return input("Enter the value you would like to submit: \n")

    def validate_input(self, abi_type: str, user_input: str) -> Tuple[Any, Any]:
        """Parse input and validate user responses"""
        status = ResponseStatus()
        if is_length_greater_than_one(abi_type.strip('()').split(",")):
            _type = abi_type.strip('()').split(",")
            try:
                usr_input = list(literal_eval(user_input))
            except ValueError as e:
                return None, error_status(note="", e=e)

            if len(_type) != len(usr_input):
                return None, error_status(note="Not enough items in input", log=logger.error)

            for typ, inpt in zip(_type, usr_input):
                try:
                    if is_list(typ):
                        try:
                            list(map(Decimal, inpt))
                        except TypeError:
                            note = f"Invalid input-> {inpt}; Should be a list"
                            return None, error_status(note=note, log=logger.error)
                        encode_single(f'({typ})', [inpt])
                    else:
                        encode_single(f'({typ})', [Decimal(inpt)])
                except Exception as e:
                    note = f"At least one of your responses is invalid: {inpt}, should be {typ}"
                    return None, error_status(note=note, log=logger.error, e=e)
            return usr_input, status

        else:
            try:
                if is_list(abi_type):
                    user_input, status = _validate_user_input_single_item(abi_type, user_input)
                    if status.ok:
                        try:
                            encode_single(self.query.value_type.abi_type, user_input)
                            return user_input, status
                        except Exception as e:
                            note = "There was a problem encoding the input"
                            return None, error_status(note=note, e=e, log=logger.error)
                else:
                    try:
                        if len(_strip_single_item_input(user_input)) > 1:
                            return None, error_status(note="Too many values, only one decimal value required")

                        user_input = _decimal_conversion(user_input)
                        encode_single(abi_type, user_input)
                        return user_input, status
                    except Exception as e:
                        note = f"Could not encode single item input for abi type {abi_type}"
                        return None, error_status(note=note, e=e, log=logger.error)

            except Exception as e:
                return None, error_status(note="User input not valid, should be in decimals", e=e, log=logger.error)
        return None, None

    def parse_user_input(self) -> Tuple[Any, ResponseStatus]:
        """Decipher user input and determine its type"""
        user_input = self.user_input()
        if user_input == '':
            return None, error_status(note="You didn't enter anything", log=logger.error)
        abi_type = self.get_abi_type()
        data, status = self.validate_input(abi_type, user_input)
        if status.ok:
            return data, status
        return None, status

    async def fetch_new_datapoint(self) -> OptionalDataPoint[Decimal]:
        data, status = self.parse_user_input()
        if status.ok:
            datapoint = (data, datetime_now_utc())
            self.store_datapoint(datapoint)
            return datapoint
        else:
            error_status(note="Input Not valid")
            return None, None
