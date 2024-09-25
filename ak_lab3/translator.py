import shlex
import sys
from typing import List, Union, cast

from ak_lab3.isa import write_code, Instruction, Opcode, Register

command_arg_count: dict[Opcode, int] = {
    Opcode.LW: 2,
    Opcode.SW: 2,
    Opcode.IN: 2,
    Opcode.OUT: 2,
    Opcode.BEQ: 3,
    Opcode.BGE: 3,
    Opcode.JMP: 1,
    Opcode.ADD: 3,
    Opcode.SUB: 3,
    Opcode.MUL: 3,
    Opcode.DIV: 3,
    Opcode.HLT: 0,
    Opcode.WORD: 1,
}


def remove_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def preprocess_tokenize(text: str) -> list[list[str]]:
    data = [remove_comment(str(line_raw)) for line_raw in text.splitlines()]
    data = [line.replace("\t", " ").replace(",", "") for line in data]
    data = [" ".join(line.split()) for line in data]
    data = [line for line in data if line != ""]
    # shlex.split splits by whitespaces if they are not between "
    tokens = list(map(shlex.split, data))
    return tokens


def parse_word_data(data: str) -> list[Instruction]:
    if data.isdigit():
        return [Instruction(Opcode.WORD, [int(data)])]
    return list(Instruction(Opcode.WORD, [i]) for i in map(ord, data))


def parse_tokens(tokens: list[list[str]]) -> tuple[list[Instruction], dict[str, int]]:
    code: list[Instruction] = []
    labels_mapping: dict[str, int] = {}
    for line in tokens:
        if line[0].endswith(":"):
            label_name = line[0][:-1]
            labels_mapping[label_name] = len(code)
            line.pop(0)
        assert len(line) > 0, "Labels and code must be on one line!"
        if line[0] == "times":
            code += [Instruction(Opcode.WORD, [int(line[-1])])] * int(line[1])
            continue
        if line[0] == "dd":
            for word_data in map(parse_word_data, line[1:]):
                code += word_data
            continue
        op, *args = line
        code.append(Instruction(Opcode(op), cast(List[Union[int, str, Register]], args)))
    return code, labels_mapping


def validate_instructions(instructions: list[Instruction]) -> bool:
    for instruction in instructions:
        if instruction.opcode not in command_arg_count:
            raise NotImplementedError(f"Instruction {instruction.opcode} not implemented")
        if command_arg_count[instruction.opcode] != len(instruction.args):
            print("Инструкция имеет неверное количество аргументов!: ", instruction)
            return False
    return True


def parse_instruction_args(instructions: list[Instruction]):
    for instruction in instructions:
        if instruction.args is None:
            continue
        if len(instruction.args) > 0 and isinstance(instruction.args[-1], str):
            if instruction.args[-1].isdigit():
                instruction.args[-1] = int(instruction.args[-1])
                continue
        instruction.args = list(map(
            lambda arg: Register(arg)
            if Register.has_value(arg) and isinstance(arg, str)
            else arg,
            instruction.args
        ))


def map_labels(instructions: list[Instruction], labels_mapping: dict[str, int]):
    for instruction in instructions:
        if len(instruction.args) == 0:
            continue
        if isinstance(instruction.args[-1], str) and not isinstance(instruction.args[-1], Register):
            assert instruction.args[-1] in labels_mapping, "Unknown label: " + instruction.args[-1]
            instruction.args[-1] = labels_mapping[instruction.args[-1]]


def translate(text: str) -> dict:
    tokens = preprocess_tokenize(text)
    code, labels_mapping = parse_tokens(tokens)
    assert "_start" in labels_mapping, "No start label!"
    if not validate_instructions(code):
        sys.exit(1)
    parse_instruction_args(code)
    map_labels(code, labels_mapping)
    return {
        "code": code,
        "start": labels_mapping["_start"]
    }


def main(source: str, target: str):
    with open(source, 'r', encoding='utf-8') as f:
        code = f.read()
    program_translated = translate(code)
    write_code(target, program_translated)


if __name__ == '__main__':
    assert (
            len(sys.argv) == 3
    ), "Wrong arguments: translator.py <input_file> <output_file>"
    main(sys.argv[1], sys.argv[2])
