import argparse
import json
import logging

from machine_modules.data_path import DataPath
from machine_modules.mux import ProgramCounterMux

logging.basicConfig(format="%(levelname)s - %(message)s", level=logging.DEBUG)


class ControlUnit:
    def __init__(self, program, data_path, max_ticks=150000):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0  # Счётчик тактов
        self.max_ticks = max_ticks  # Максимальное количество тиков
        self.output_buffer = []  # Буфер вывода для тестирования
        logging.debug("Control Unit initialized.")

    def tick(self):
        """Продвигаем модельное время вперед на один такт"""
        self._tick += 1
        logging.debug({self})

        # Проверяем, достигнуто ли максимальное количество тиков
        if self._tick >= self.max_ticks:
            logging.debug(f"Maximum tick count {self.max_ticks} reached. Halting execution.")
            raise StopIteration()

    def latch_pc(self, sel, value):
        """Устанавливает значение data_address в зависимости от состояния селектора"""
        if isinstance(sel, str):  # Если передана строка
            sel_mux = ProgramCounterMux()
            sel_mux.handle_input(sel)
        else:
            sel_mux = sel  # Если это уже объект DAMux

        if sel_mux.state == "INC":
            self.program_counter += 1
        elif sel_mux.state == "MEM":
            self.program_counter = value

    def decode_and_execute_control_flow_instruction(self, instr, opcode):
        """Декодировать и выполнить инструкцию управления потоком исполнения."""
        logging.debug(f"Executing control flow instruction: {opcode} at PC: {self.program_counter}")

        if opcode == "hlt":
            logging.debug("HLT instruction encountered. Halting execution.")
            raise StopIteration()

        if opcode == "jmp":
            addr = instr["addr"]
            logging.debug(f"JMP to address: {addr}")
            self.latch_pc("MEM", addr)
            self.tick()
            return True

        if opcode == "je":
            addr = instr["addr"]
            if self.data_path.zero_flag:
                logging.debug(f"JE condition met. Jumping to address: {addr}")
                self.latch_pc("MEM", addr)
                self.tick()
            else:
                logging.debug("JE condition not met. Incrementing PC.")
                self.latch_pc("INC", None)
                self.tick()
            return True
        if opcode == "jne":
            addr = instr["addr"]
            if not self.data_path.zero_flag:
                logging.debug(f"JNE condition met.Jumping to address: {addr} ")
                self.latch_pc("MEM", addr)
                self.tick()
            else:
                logging.debug("JNE condition not met. Incrementing PC.")
                self.latch_pc("INC", None)
                self.tick()
            return True
        if opcode == "jb":
            addr = instr["addr"]
            if self.data_path.negative_flag:
                logging.debug(f"JB condition met. Jumping to address: {addr}")
                self.latch_pc("MEM", addr)
                self.tick()
            else:
                logging.debug("JB condition not met. Incrementing PC.")
                self.latch_pc("INC", None)
                self.tick()
            return True

        return False

    def operand_fetch(self, instr):
        """Получение операндов в зависимости от режима адресации."""
        if instr["addr_mode"] == "direct":
            # Прямой доступ к адресу
            self.data_path.latch_da("CU", instr["addr"])
            self.tick()
        elif instr["addr_mode"] == "indirect":
            # Прямой доступ к адресу
            self.data_path.latch_da("CU", instr["addr"])
            self.tick()

            # Загружаем значение из памяти в регистр данных
            self.data_path.latch_dr("MEM", self.data_path.get_operand_from_memory())
            self.tick()

            # Переключаем адрес на значение из регистра данных
            self.data_path.latch_da("DR", self.data_path.data_register)
            self.tick()
        elif instr["addr_mode"] == "immediate":
            # Непосредственная передача данных
            self.data_path.latch_dr("CU", instr["addr"])
            self.tick()
        else:
            return

    def decode_and_execute_instruction(self):
        """Основной цикл процессора. Декодирует и выполняет инструкцию."""
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        logging.debug(f"Decoding instruction at PC: {self.program_counter} - Opcode: {opcode}")

        # Проверка инструкций управления потоком
        if self.decode_and_execute_control_flow_instruction(instr, opcode):
            return

        # Обработка остальных инструкций
        if opcode == "ld":
            logging.debug(f"Executing LD instruction. Address mode: {instr['addr_mode']}")

            # Получение операндов на основе режима адресации
            self.operand_fetch(instr)

            # Проверка на ввод
            if self.data_path.data_address == self.data_path.input_adr:
                self.data_path.next_input()
                self.data_path.latch_acc("MEM")
                self.data_path.data_memory[self.data_path.input_adr] = self.data_path.input_adr
                self.tick()
            else:
                # Загружаем данные в аккумулятор из памяти
                self.data_path.latch_acc("MEM")
                self.tick()

            # Увеличиваем программный счётчик
            self.latch_pc("INC", None)
            self.tick()

        # Обработка инструкций хранения (ST)

        elif opcode == "st":
            logging.debug(f"Executing ST instruction. Address mode: {instr['addr_mode']}")
            # Получение операндов на основе режима адресации
            self.operand_fetch(instr)
            # Выполняем запись данных из аккумулятора в память
            self.data_path.write_to_memory()
            logging.debug(f"Stored accumulator data into memory at address {self.data_path.data_address}.")
            self.data_path.check_output()
            self.tick()

            # Увеличиваем программный счётчик
            self.latch_pc("INC", None)
            self.tick()

        elif opcode == "cmp":
            if instr["addr_mode"] == "immediate":
                self.data_path.latch_dr("CU", instr["addr"])
                self.tick()
                self.data_path.alu_compare()
                self.tick()
                self.latch_pc("INC", None)
                self.tick()

            if instr["addr_mode"] == "indirect":
                self.data_path.latch_da("CU", instr["addr"])
                logging.debug(f"Latching data address directly: {instr['addr']}")
                self.tick()

                # Загружаем значение из памяти в регистр данных
                self.data_path.latch_dr("MEM", self.data_path.get_operand_from_memory())
                self.tick()

                # Переключаем адрес на значение из регистра данных
                self.data_path.latch_da("DR", self.data_path.data_register)
                logging.debug(f"Latching data address from DR: {self.data_path.data_register}")
                self.tick()

                # Проверка ввода
                if self.data_path.data_address == self.data_path.input_adr:
                    self.data_path.next_input()
                self.data_path.latch_dr("MEM", self.data_path.get_operand_from_memory())
                self.tick()
                self.data_path.alu_compare()
                self.tick()
                self.latch_pc("INC", None)
                self.tick()

            if instr["addr_mode"] == "direct":
                self.data_path.latch_da("CU", instr["addr"])  # Прямой доступ к адресу
                logging.debug(f"Latching data address directly: {instr['addr']}")
                self.tick()

                # Проверка ввода
                if self.data_path.data_address == self.data_path.input_adr:
                    self.data_path.next_input()

                self.data_path.latch_dr("CU", instr["addr"])
                self.tick()
                self.data_path.alu_compare()
                self.tick()
                self.latch_pc("INC", None)
                self.tick()

        elif opcode == "inc":
            self.data_path.latch_acc("NONE")
            self.tick()
            self.data_path.alu_inc()
            self.tick()
            self.latch_pc("INC", None)

            self.tick()
        elif opcode == "add":
            if instr["addr_mode"] == "immediate":
                self.data_path.latch_dr("CU", instr["addr"])
                self.tick()
                self.data_path.alu_add()
                self.tick()
                self.latch_pc("INC", None)
                self.tick()
            if instr["addr_mode"] == "indirect":
                self.data_path.latch_da("CU", instr["addr"])
                self.tick()
                if self.data_path.data_address == self.data_path.input_adr:
                    self.data_path.next_input()
                # Загружаем данные в аккумулятор из памяти
                self.data_path.latch_dr("MEM", self.data_path.get_operand_from_memory())
                self.tick()
                self.data_path.latch_da("DR", self.data_path.data_register)
                self.tick()
                self.data_path.latch_dr("MEM", self.data_path.get_operand_from_memory())
                self.tick()
                self.data_path.alu_add()
                self.tick()
                self.latch_pc("INC", None)
                self.tick()
        elif opcode == "mod":
            if instr["addr_mode"] == "immediate":
                self.data_path.latch_dr("CU", instr["addr"])
                self.tick()
                self.data_path.alu_mod()
                self.tick()
                self.latch_pc("INC", None)
                self.tick()

    def run(self):
        """
        Запускает выполнение программы
        """
        logging.debug("Starting program execution.")
        try:
            while self.program_counter < len(self.program):
                self.decode_and_execute_instruction()
                logging.debug(f"Control Unit state: {self}")
        except StopIteration:
            logging.debug("Program halted.")

        output_string = "".join(str(i) for i in self.data_path.output_buffer)

        # Заменяем нулевые символы перед логированием
        output_string = output_string.replace("\u0000", "\\u0000")

        logging.debug(f"Program finished. Output buffer contents: {output_string}")

        self.output_buffer = output_string  # Сохранение результата для тестов
        print(f"Output: {output_string}")  # Вывод в stdout
        return output_string  # Возвращение вывода для тестов

    def __repr__(self):
        return "{{TICK: {}, PC: {}, ADDR: {}, ACC: {}, DR: {}, DA: {}}}".format(
            self._tick,
            self.program_counter,
            self.data_path.data_address,
            self.data_path.acc,
            self.data_path.data_register,
            self.data_path.data_address,
        )


def parse_arguments():
    """Функция для обработки аргументов командной строки."""
    parser = argparse.ArgumentParser(description="Run machine simulation.")

    parser.add_argument(
        "machine_code_file",
        type=str,
        help="Path to the machine code file (instructions).",
    )

    parser.add_argument("input_file", type=str, help="Path to the input file with data for the machine.")

    return parser.parse_args()


def main():
    """Основная функция для запуска симуляции машины."""
    # Получение аргументов
    args = parse_arguments()

    # Чтение файла с машинным кодом (инструкциями)
    with open(args.machine_code_file, encoding="utf-8") as f:
        machine_code = json.load(f)
        logging.debug(f"Machine code loaded from {args.machine_code_file}")

    # Чтение файла с входными данными для симуляции
    with open(args.input_file, encoding="utf-8") as f:
        input_data = f.read().splitlines()  # Чтение данных как строки
        logging.debug(f"Input data loaded from {input_data}")

    # Инициализация DataPath с входными данными
    data_path = DataPath("output_compiler_memory.json", args.input_file)

    # Инициализация ControlUnit с машинным кодом и DataPath
    control_unit = ControlUnit(machine_code["instructions"], data_path)

    # Запуск симуляции
    output = control_unit.run()

    # Вывод результата
    logging.debug(f"Machine output: {output}")
    print(output)


if __name__ == "__main__":
    main()
