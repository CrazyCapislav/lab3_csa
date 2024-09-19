import json


class MemoryConfigurator:
    def __init__(self, json_file):
        self.data_memory_size = 128
        self.instr_memory_size = 128
        self.input_adr = 126
        self.output_adr = 127
        self.cur_adr = 125
        self.data_memory = [0] * self.data_memory_size
        self.instr_memory = [None] * self.instr_memory_size

        # Чтение данных из JSON-файла
        self.load_from_json(json_file)

    def load_from_json(self, json_file):
        # Загрузка данных из JSON-файла
        with open(json_file) as file:
            data = json.load(file)

        # Заполнение массива data_memory
        data_list = data.get("data", [])
        if len(data_list) > self.data_memory_size:
            raise ValueError(
                f"Ошибка: количество данных ({len(data_list)}) "
                f"превышает размер буфера для data ({self.data_memory_size})"
            )

        for index, value in enumerate(data_list):
            if index < self.data_memory_size:
                self.data_memory[index] = value

        self.data_memory[self.input_adr] = "IN_ADR"
        self.data_memory[self.output_adr] = "OUT_ADR"
        self.data_memory[self.cur_adr] = "CUR_ADR"

        # Заполнение массива instr_memory
        instructions = data.get("instructions", [])
        if len(instructions) > self.instr_memory_size:
            raise ValueError(
                f"Ошибка: количество инструкций ({len(instructions)}) "
                f"превышает размер буфера для instructions ({self.instr_memory_size})"
            )

        for instr in instructions:
            if instr["curr_addr"] < self.instr_memory_size:
                self.instr_memory[instr["curr_addr"]] = instr

    def get_data_memory(self):
        return self.data_memory

    def get_instr_memory(self):
        return self.instr_memory

    def save_data_to_json(self, output_file):
        """Сохраняет секцию данных в отдельный JSON-файл"""
        data_output = {
            "data": [value for value in self.data_memory if value is not None or value == "input" or value == "output"]
        }
        with open(output_file, "w") as file:
            json.dump(data_output, file, ensure_ascii=False, indent=4)

    def save_instructions_to_json(self, output_file):
        """Сохраняет секцию инструкций в отдельный JSON-файл"""
        instructions_output = {
            "instructions": [
                {
                    "curr_addr": instr["curr_addr"],
                    "opcode": instr["opcode"],
                    "addr": self._replace_labels(instr.get("addr")),
                    "addr_mode": instr.get("addr_mode"),
                }
                for instr in self.instr_memory
                if instr is not None and isinstance(instr, dict) and "opcode" in instr
            ]
        }
        with open(output_file, "w") as file:
            json.dump(instructions_output, file, ensure_ascii=False, indent=4)

    def _replace_labels(self, addr):
        """Заменяет метки IN_ADR, OUT_ADR и CUR_ADR на соответствующие числовые значения"""
        if addr == "IN_ADR":
            return self.input_adr
        if addr == "OUT_ADR":
            return self.output_adr
        if addr == "CUR_ADR":
            return self.cur_adr
        return addr
