import json
from dataclasses import dataclass, asdict
from enum import StrEnum, auto, Enum
from typing import Union, List

IO_OUT_PORT = 0
IO_IN_PORT = 1
SIMULATION_LIMIT = 500


class Opcode(StrEnum):
    LW = auto()
    SW = auto()
    IN = auto()
    OUT = auto()
    BEQ = auto()
    BGE = auto()
    JMP = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    HLT = auto()
    WORD = auto()


class Register(StrEnum):
    R0 = auto()
    R1 = auto()
    R2 = auto()
    R3 = auto()
    R4 = auto()
    R5 = auto()
    R6 = auto()
    R7 = auto()

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_


    def __repr__(self):
        return self.name



@dataclass
class Instruction:
    opcode: Opcode
    args: List[Union[int, str, Register]]


    def to_dict(self):
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}

    @staticmethod
    def from_dict(data: dict):
        assert "opcode" in data, "No opcode in instruction!"
        args = data["args"]
        for i, arg in enumerate(args):
            if Register.has_value(arg):
                args[i] = Register(arg)
        return Instruction(data["opcode"], args)

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Instruction):
            return o.to_dict()
        if isinstance(o, Enum):
            return o.value
        return json.JSONEncoder.default(self, o)


def write_code(filename: str, code: dict) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(code, cls=CustomEncoder, indent=2))


def read_code(filename: str) -> tuple[list[Instruction], int]:
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)
    code = list(map(Instruction.from_dict, data["code"]))
    return code, data["start"]
