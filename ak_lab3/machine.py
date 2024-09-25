import logging
import sys
from collections import deque
from typing import Callable, Optional

from ak_lab3.isa import (read_code, Instruction,
                         Register, Opcode,
                         IO_OUT_PORT, IO_IN_PORT, SIMULATION_LIMIT)


class ALU:
    _z_flag: bool = False
    _n_flag: bool = False

    _operations_ = {
        Opcode.ADD: lambda a, b: a + b,
        Opcode.SUB: lambda a, b: a - b,
        Opcode.MUL: lambda a, b: a * b,
        Opcode.DIV: lambda a, b: a // b,
    }

    def compute(self, left: int, right: int, operation: Opcode) -> int:
        res = int(self._operations_[operation](left, right))
        self._z_flag = res == 0
        self._n_flag = res > 0
        return res

    @property
    def z_flag(self) -> bool:
        return self._z_flag

    @property
    def n_flag(self) -> bool:
        return self._n_flag


class IO:
    input_buffer: deque

    def __init__(self, input_tokens: list):
        self.input_buffer = deque(input_tokens)
        self.output_buffer: deque[int] = deque()

    def eof(self) -> bool:
        return not self.input_buffer

    def input(self) -> int:
        return self.input_buffer.popleft()

    def output(self, character):
        self.output_buffer.append(character)

    def get_buffer(self) -> str | deque:
        if all(map(lambda i: 0 <= i <= ord('z'), self.output_buffer)):
            return "".join(map(chr, self.output_buffer))
        return self.output_buffer


class DataPath:
    _memory: list[Instruction]
    _registers: dict[Register, int] = {
        Register.R0: 0,
        Register.R1: 0,
        Register.R2: 0,
        Register.R3: 0,
        Register.R4: 0,
        Register.R5: 0,
        Register.R6: 0,
        Register.R7: 0,
    }
    _ar: int = 0
    _pc: int = 0
    _io: dict[int, IO]
    _alu: ALU

    def __init__(self, memory: list[Instruction], io: dict[int, IO], alu: ALU, start: int) -> None:
        self._memory = memory
        self._io = io
        self._alu = alu
        self._pc = start

    def read_memory(self) -> Instruction | int:
        data = self._memory[self._ar]
        if data.opcode == Opcode.WORD:
            assert isinstance(data.args[0], int)
            return data.args[0]
        return data

    def write_memory(self, value: int):
        self._memory[self._ar] = Instruction(Opcode.WORD, [value])

    def latch_ar(self, value: int):
        self._ar = value

    def latch_pc(self, value: int):
        self._pc = value

    def alu_compute(self, opcode: Opcode, left: int, right: int) -> int:
        return self._alu.compute(left, right, opcode)

    def latch_r(self, r: Register, value: int):
        assert r != Register.R0, "Writing to r0 is prohibited!"
        self._registers[r] = value

    @property
    def registers(self) -> dict[Register, int]:
        return self._registers

    @property
    def pc(self) -> int:
        return self._pc

    @property
    def ar(self) -> int:
        return self._ar

    @property
    def io(self) -> dict[int, IO]:
        return self._io

    @property
    def alu(self) -> ALU:
        return self._alu

    @property
    def memory(self) -> list[Instruction]:
        return self._memory


class ControlUnit:
    data_path: DataPath
    _tick: int = 0
    _current_instruction: Optional[Instruction]
    _instruction_handlers_: dict[Opcode, Callable[[], None]]

    def __init__(self, data_path: DataPath):
        self.data_path = data_path
        self._instruction_handlers_ = {
            Opcode.LW: self.handle_lw,
            Opcode.SW: self.handle_sw,
            Opcode.IN: self.handle_in,
            Opcode.OUT: self.handle_out,
            Opcode.BEQ: self.handle_beq,
            Opcode.BGE: self.handle_bge,
            Opcode.JMP: self.handle_jmp,
            Opcode.ADD: self.handle_alu_op,
            Opcode.SUB: self.handle_alu_op,
            Opcode.MUL: self.handle_alu_op,
            Opcode.DIV: self.handle_alu_op,
            Opcode.HLT: self.handle_hlt,
            Opcode.WORD: self.handle_word,
        }
        self._current_instruction = None

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def decode_and_execute_instruction(self):
        self.data_path.latch_ar(self.data_path.pc)
        self.tick()
        self.data_path.latch_pc(self.data_path.pc + 1)
        self.tick()
        self._current_instruction = self.data_path.read_memory()
        self.tick()
        assert self._current_instruction.opcode != Opcode.WORD, "Executing data!"
        assert self._current_instruction.opcode in self._instruction_handlers_, \
            "That op is not implemented!"
        self._instruction_handlers_[self._current_instruction.opcode]()

    def handle_lw(self):
        self.data_path.latch_ar(
            self.data_path.registers[self._current_instruction.args[1]]
        )
        self.tick()
        self.data_path.latch_r(self._current_instruction.args[0],
                               self.data_path.read_memory())
        self.tick()

    def handle_sw(self):
        self.data_path.latch_ar(
            self.data_path.registers[self._current_instruction.args[0]]
        )
        self.tick()
        self.data_path.write_memory(
            self.data_path.registers[self._current_instruction.args[1]]
        )
        self.tick()

    def handle_in(self):
        self.data_path.latch_r(
            self._current_instruction.args[0],
            self.data_path.io[self._current_instruction.args[1]].input()
        )
        self.tick()

    def handle_out(self):
        self.data_path.io[self._current_instruction.args[1]].output(
            self.data_path.registers[self._current_instruction.args[0]]
        )
        self.tick()

    def handle_beq(self):
        self.data_path.alu_compute(
            Opcode.SUB,
            self.data_path.registers[self._current_instruction.args[0]],
            self.data_path.registers[self._current_instruction.args[1]],
        )
        self.tick()
        if self.data_path.alu.z_flag:
            self.data_path.latch_pc(self._current_instruction.args[2])
            self.tick()

    def handle_bge(self):
        self.data_path.alu_compute(
            Opcode.SUB,
            self.data_path.registers[self._current_instruction.args[0]],
            self.data_path.registers[self._current_instruction.args[1]],
        )
        self.tick()
        if self.data_path.alu.n_flag:
            self.data_path.latch_pc(self._current_instruction.args[2])
            self.tick()

    def handle_jmp(self):
        self.data_path.latch_pc(self._current_instruction.args[0])
        self.tick()

    def handle_alu_op(self):
        if isinstance(self._current_instruction.args[2], int):
            right = self._current_instruction.args[2]
        else:
            right = self.data_path.registers[self._current_instruction.args[2]]
        self.data_path.latch_r(
            self._current_instruction.args[0],
            self.data_path.alu_compute(
                self._current_instruction.opcode,
                self.data_path.registers[self._current_instruction.args[1]],
                right,
            )
        )
        self.tick()

    def handle_hlt(self):
        raise StopIteration

    def handle_word(self):
        raise NotImplementedError

    def __repr__(self):
        state_repr = (
            f"TICK: {self.current_tick():4} "
            f"PC: {self.data_path.pc:4} "
            f"AR: {self.data_path.ar:4} "
            f"Z_FLAG: {self.data_path.alu.z_flag:1} "
            f"N_FLAG: {self.data_path.alu.n_flag:1} "
        )
        # registers_repr = "".join(
        #     f"{reg.capitalize()}: {value:8} "
        #     for reg, value in self.data_path.registers.items()
        #     if reg not in (Register.R0, Register.R6, Register.R7)
        # )

        return f"{state_repr} \t{self._current_instruction.__repr__():40}"


def simulation(code: list[Instruction], input_buffer: list[int], start: int):
    ios = {
        IO_OUT_PORT: IO([]),
        IO_IN_PORT: IO(input_buffer)
    }
    alu = ALU()
    data_path = DataPath(code, ios, alu, start)
    control_unit = ControlUnit(data_path)
    instr_counter = 0
    logging.debug("%s", control_unit)
    try:
        while instr_counter < SIMULATION_LIMIT:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is name!")
    except StopIteration:
        pass

    if instr_counter >= SIMULATION_LIMIT:
        logging.warning("Limit exceeded!")
    logging.info("output buffer: %s", ios[IO_OUT_PORT].get_buffer())


def main(code_file: str, input_file: str):
    code, start = read_code(code_file)

    with open(input_file, encoding="ascii") as f:
        text = f.read()
        input_buffer = [ord(c) for c in text]
        input_buffer.append(0)

    simulation(code, input_buffer, start)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Usage: machine.py <input_file> <input>"
    main(sys.argv[1], sys.argv[2])
