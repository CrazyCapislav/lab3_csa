import json
import logging

from machine_modules.mux import AccMux, DAMux, DRMux


class DataPath:
    def __init__(self, json_data_or_file, input_buffer):
        self.data_memory = [0] * 128  # 128 ячеек памяти
        self.input_buffer = input_buffer
        self.output_buffer = []
        self.data_register = 0
        self.acc = 0  # Аккумулятор
        self.data_address = 0
        self.alu = 0
        self.zero_flag = False
        self.negative_flag = False

        # Специальные адреса для работы с I/O
        self.cur_adr = 125
        self.input_adr = 126
        self.output_adr = 127

        self.cur_symbol = 0

        # Проверка, является ли переданный аргумент путем к файлу
        if isinstance(json_data_or_file, str):
            # Если это строка, предполагаем, что это путь к файлу
            self.load_data_from_file(json_data_or_file)
        else:
            # Иначе считаем, что это уже загруженный JSON-объект
            self.load_data_from_json(json_data_or_file)

    def load_data_from_file(self, file_path):
        """Загрузка данных из JSON-файла"""
        logging.info(f"Загрузка данных из файла: {file_path}")
        try:
            with open(file_path) as file:
                json_data = json.load(file)
                self.load_data_from_json(json_data)
        except FileNotFoundError:
            logging.exception(f"Файл {file_path} не найден.")
        except json.JSONDecodeError:
            logging.exception(f"Ошибка при декодировании JSON из файла {file_path}.")

    def load_data_from_json(self, json_data):
        """Загрузка данных в память на основе предоставленного JSON и вывод данных в лог"""
        data_list = json_data.get("data", [])
        logging.info("Начинаем инициализацию памяти...")

        for i, value in enumerate(data_list):
            if i >= len(self.data_memory):
                break  # Не допускаем выхода за границы памяти

            # Обработка специальных меток
            if value == "CUR_ADR":
                self.data_memory[i] = self.cur_adr
                logging.info(f"Memory[{i}] initialized with CUR_ADR ({self.cur_adr})")
            elif value == "IN_ADR":
                self.data_memory[i] = self.input_adr
                logging.info(f"Memory[{i}] initialized with IN_ADR ({self.input_adr})")
            elif value == "OUT_ADR":
                self.data_memory[i] = self.output_adr
                logging.info(f"Memory[{i}] initialized with OUT_ADR ({self.output_adr})")
            else:
                self.data_memory[i] = value

        logging.info("Инициализация памяти завершена.")
        logging.info(f"Initialized memory: {self.data_memory}")

    def update_flags(self, result):
        """Обновляет флаги zero и negative на основе результата"""
        # Обрабатываем только числовые значения
        if isinstance(result, (int, float)):
            self.zero_flag = result == 0
            self.negative_flag = result < 0
        else:
            # Если это строка или другой тип, мы не можем установить флаги, основанные на числовых операциях
            self.zero_flag = False
            self.negative_flag = False
            logging.warning(f"Cannot update flags for non-numeric result: {result}")

    def latch_da(self, sel, value):
        """Устанавливает значение data_address в зависимости от состояния селектора"""
        if isinstance(sel, str):  # Если передана строка
            sel_mux = DAMux()
            sel_mux.handle_input(sel)
        else:
            sel_mux = sel  # Если это уже объект DAMux

        if sel_mux.state == "CU":
            # Прямое присваивание строки в data_address, если это строка
            self.data_address = value  # Теперь self.data_address может быть строкой или числом
        elif sel_mux.state == "DR":
            self.data_address = self.data_register

    def latch_dr(self, sel, value):
        """Устанавливает значение data_register в зависимости от состояния селектора"""
        if isinstance(sel, str):  # Если передана строка
            sel_mux = DRMux()  # Создаём объект DRMux
            sel_mux.handle_input(sel)
        else:
            sel_mux = sel  # Если это уже объект DAMux

        if sel_mux.state == "CU":
            # Прямое присваивание строки в data_address, если это строка
            self.data_register = value  # Теперь self.data_address может быть строкой или числом
        elif sel_mux.state == "MEM":
            self.data_register = self.data_memory[self.data_address]

    def latch_acc(self, sel):
        """Устанавливает значение аккумулятора в зависимости от состояния селектора"""
        if isinstance(sel, str):
            sel_mux = AccMux()
            sel_mux.handle_input(sel)
        else:
            sel_mux = sel

        if sel_mux.state == "NONE":
            return

        if sel_mux.state == "ALU":
            self.acc = self.alu
        elif sel_mux.state == "MEM":
            self.acc = self.data_memory[self.data_address]

    def write_to_memory(self):
        """Записывает текущее значение аккумулятора в память"""
        self.data_memory[self.data_address] = self.acc

    def check_output(self):
        """Записывает текущее значение аккумулятора в память"""
        output_value = self.data_memory[self.output_adr]
        output = self.output_buffer
        if output_value != self.output_adr:  # Проверяем, изменилось ли значение
            logging.info(f"New output detected at address {self.output_adr}: {output_value}")
            output.append(output_value)  # Добавляем в буфер
            self.data_memory[self.output_adr] = self.output_adr  # Сбрасываем значение после записи
            logging.info(f"OUTPUT: {self.output_buffer}")

    def next_input(self):
        """Читает следующий символ из input_buffer и записывает его в data_memory по адресу input_adr"""
        if self.cur_symbol < len(self.input_buffer):
            self.data_memory[self.input_adr] = self.input_buffer[self.cur_symbol]
            logging.info(
                f"Input[{self.cur_symbol}]: "
                f"{self.input_buffer[self.cur_symbol]} added to memory at address {self.input_adr}"
            )
            self.cur_symbol += 1
        else:
            logging.info("Input ends already")

    def get_operand_from_memory(self):
        """Возвращает значение из памяти по текущему адресу"""
        return self.data_memory[self.data_address]

    def alu_inc(self):
        """Выполняет операцию"""
        self.acc = self.acc + 1
        self.alu = self.acc
        self.update_flags(self.alu)

    def alu_add(self):
        """Выполняет операцию сложения ALU"""
        self.alu = self.acc + self.data_register
        self.acc = self.alu
        self.update_flags(self.alu)

    def alu_sub(self):
        """Выполняет операцию вычитания ALU"""
        self.alu = self.acc - self.data_register
        self.update_flags(self.alu)

    def alu_div(self):
        """Выполняет операцию деления ALU с проверкой деления на ноль"""
        if self.data_register == 0:
            raise ZeroDivisionError({self.data_register})
        self.alu = self.acc // self.data_register
        self.update_flags(self.alu)

    def alu_mod(self):
        """Выполняет операцию вычисления остатка от деления ALU с проверкой деления на ноль"""
        if self.data_register == 0:
            raise ZeroDivisionError({self.data_register})
        self.alu = self.acc % self.data_register
        self.acc = self.alu
        self.update_flags(self.alu)

    def alu_mul(self):
        """Выполняет операцию умножения ALU"""
        self.alu = self.acc * self.data_register
        self.update_flags(self.alu)

    def alu_compare(self):
        """Выполняет операцию сравнения для команды CMP, поддерживает числа и строки"""

        # Проверяем, если оба операнда строки
        if isinstance(self.acc, str) and isinstance(self.data_register, str):
            if self.acc == self.data_register:
                result = 0
            elif self.acc < self.data_register:
                result = -1
            else:
                result = 1
        # Если оба операнда числа
        elif isinstance(self.acc, (int, float)) and isinstance(self.data_register, (int, float)):
            result = self.acc - self.data_register
        else:
            raise TypeError(f"Невозможно сравнить значения разных типов: {type(self.acc)} и {type(self.data_register)}")

        # Обновляем флаги на основе результата
        self.update_flags(result)
