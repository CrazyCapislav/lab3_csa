import json
from enum import Enum


class Opcode(str, Enum):
    # Арифметика
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"

    MOD = "mod"

    INC = "inc"

    CMP = "cmp"

    # Память
    LD = "ld"
    ST = "st"

    # Переходы
    JMP = "jmp"
    JNE = "jne"
    JE = "je"
    JB = "jb"

    HLT = "hlt"

    def __str__(self):
        return str(self.value)


class AddressingMode(str, Enum):
    immediate_addressing = "immediate"
    direct_addressing = "direct"
    indirect_addressing = "indirect"

    def __str__(self):
        return str(self.value)


def write_code(code_filename, code, data_filename, data):
    with open(code_filename, "w", encoding="utf-8") as code_file:
        json.dump(code, code_file, ensure_ascii=False, indent=4)
        code_file.write("\n")
    with open(data_filename, "w", encoding="utf-8") as data_file:
        json.dump(data, data_file, ensure_ascii=False, indent=4)


def read_code(code_filename, data_filename):
    with open(code_filename, encoding="utf-8") as code_file:
        code = json.loads(code_file.read())

    for instr in code:
        # Конвертация строки в Opcode
        instr["opcode"] = Opcode(instr["opcode"])

        if "addr_mode" in instr:
            instr["addr_mode"] = AddressingMode(instr["addr_mode"])

    with open(data_filename, encoding="utf-8") as data_file:
        data_section = json.loads(data_file.read())

    return data_section, code
