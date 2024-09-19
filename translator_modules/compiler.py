import json

from isa import AddressingMode, Opcode


class Compiler:
    def __init__(self, instructions_filename):
        self.instructions_filename = instructions_filename
        self.data_filename = instructions_filename
        self.instructions_list = []
        self.label_addresses = {}  # Словарь для хранения адресов инструкций
        self.data_labels = []
        self.current_address = 0  # Счетчик для адресов данных
        self.data_index = 0  # Индекс для секции данных
        self.compiled_data = []  # Структура для сохранения результата
        self._parse_data_file()
        self._parse_instructions_file()

    def _parse_data_file(self):
        with open(self.data_filename, encoding="utf-8") as file:
            data = json.load(file)
            self._collect_data_labels(data["labels"], data["data_section"])

    def _collect_data_labels(self, labels, data_section):
        """Собирает метки данных и корректные адреса"""

        label_counter = 0
        data_mapping = {}  # Словарь для сопоставления адресов и данных
        cur_step = 1
        # Создаем карту данных для удобного доступа по адресу
        for index, data in enumerate(data_section):
            address = self.current_address + index
            data_mapping[address] = data["value"]
        for label in labels:
            if "address" in label:
                label_counter += 1
                label_name = label["label"]
                label_address = label["address"]

                # Проверяем, существует ли указанный адрес в карте данных
                if label_address in data_mapping:
                    data_value = data_mapping[label_address]
                    # Проверяем, является ли строка неопределенной
                    if isinstance(data_value, int):
                        data_value = [0] * 1
                    else:
                        if len(data_value) == 0 and data_section[self.data_index]["type"] == "string":
                            data_value = [""] * 16  # Заменяем на массив из 16 нулевых байтов
                        elif len(data_value) == 0 and data_section[self.data_index]["type"] == "int":
                            data_value = [0] * 1
                    # Добавляем текущий адрес в список меток
                    self.data_labels.append(([label_name, label_address + cur_step], data_value))
                    self.compiled_data.append(([label_name, label_address + cur_step], data_value))
                    cur_step += len(data_value)
                    self.data_index += 1

    def _parse_instructions_file(self):
        with open(self.instructions_filename, encoding="utf-8") as file:
            data = json.load(file)
            self._collect_label_addresses(data["program_code"])
            self._parse_program_code(data["program_code"])

    def _collect_label_addresses(self, program_code):
        """Собирает адреса инструкций"""
        curr_addr = 0
        for instr in program_code:
            if "label" in instr:
                # Сохраняем адрес для метки
                self.label_addresses[instr["label"]] = curr_addr
            if "opcode" in instr:
                curr_addr += 1

    def _parse_program_code(self, program_code):
        curr_addr = 0

        for instr in program_code:
            if "opcode" in instr:
                opcode = Opcode(instr["opcode"])
                instruction = {"opcode": opcode, "curr_addr": curr_addr}

                if "operand" in instr:
                    operand = instr["operand"]
                    # Заменяем метку данных на ее адрес, если она присутствует в DataCompiler
                    data_label = self._find_data_label(operand)
                    if data_label is not None:
                        instruction["addr"] = data_label[0][1] - 1  # Используем значение адреса метки из DataCompiler
                    elif operand in self.label_addresses:
                        instruction["addr"] = self.label_addresses[operand]
                    else:
                        instruction["addr"] = operand

                if "addr_mode" in instr:
                    instruction["addr_mode"] = AddressingMode(instr["addr_mode"])

                self.instructions_list.append(instruction)
                curr_addr += 1

    def _find_data_label(self, operand):
        """Ищет метку данных в структуре DataCompiler и возвращает ее значение, если она найдена"""
        compiled_data = self.get_compiled_data()
        for label_info, data_value in compiled_data:
            if label_info[0] == operand:
                return label_info, data_value
        return None

    def get_instructions(self):
        return self.instructions_list

    def save_unified_json(self, output_filename):
        """Сохраняет данные и инструкции в единый JSON-файл"""
        unified_json = {
            "instructions": self.instructions_list,
            "data": self._flatten_data(),  # Сохраняем данные как плоский список
        }

        # Сохраняем в файл
        with open(output_filename, "w", encoding="utf-8") as output_file:
            json.dump(unified_json, output_file, ensure_ascii=False, indent=4)

    def _flatten_data(self):
        """Преобразует данные в плоский список"""
        flat_list = []
        for label_info, data_value in self.compiled_data:
            flat_list.append(label_info[1])  # Добавляем адрес
            if isinstance(data_value, list):
                flat_list.extend(data_value)  # Добавляем каждый элемент списка
            else:
                flat_list.append(data_value)  # Добавляем само значение
        return flat_list

    def get_compiled_data(self):
        return self.compiled_data
