import json

from isa import AddressingMode, Opcode
from translator_modules.ast_nodes import (
    BinaryOpNode,
    FunctionCallNode,
    IdentifierNode,
    IfElseNode,
    IfNode,
    NumberNode,
    PrintNode,
    ProgramNode,
    StringNode,
    VariableAssignNode,
    WhileNode,
)


class CodeGenerator:
    def __init__(self):
        self.code = []  # Основной код программы
        self.data = []  # Секция данных
        self.label_block = []  # Блок для меток переменных
        self.if_label_counter = 0  # Общий счётчик для создания уникальных меток
        self.print_label_counter = 0  # Счётчик для меток печати
        self.binary_op_label_counter = 0  # Счётчик для бинарных операций
        self.input_label_counter = 0  # Счётчик для бинарных операций
        self.while_label_counter = 0  # Счётчик для бинарных операций
        self.string_label_counter = 0
        self.int_label_counter = 0
        self.temp_var_int_counter = 0

    def generate(self, node):
        if isinstance(node, ProgramNode):
            # Генерация кода для каждого оператора в теле программы
            for stmt in node.statements:
                self.generate(stmt)
            # Добавление инструкции завершения программы
            self.code.append({"opcode": Opcode.HLT})  # Остановка программы
        elif isinstance(node, VariableAssignNode):
            self.generate_variable_assign(node)
        elif isinstance(node, IfElseNode):
            # Генерация кода для условного оператора if-else
            self.generate_if_else(node)
        elif isinstance(node, PrintNode):
            # Генерация кода для PRINT
            self.generate_print(node.expression)
        elif isinstance(node, IfNode):
            self.generate_if(node)
        elif isinstance(node, FunctionCallNode):
            # Генерация кода для вызова функции
            self.generate_function_call(node)
        elif isinstance(node, BinaryOpNode):
            # Генерация кода для бинарной операции
            result_var = "result_var"  # Здесь можно использовать конкретную переменную для хранения результата
            self.generate_binary_op(node, result_var)
        elif isinstance(node, WhileNode):
            # Генерация кода для бинарной операции
            self.generate_while(node)
        else:
            # Заглушка для других типов узлов
            self.code.append(
                {
                    "opcode": "NOP",
                    "comment": f"Not implemented for node {type(node).__name__}",
                }
            )

    def generate_conditional_jump(self, operator, true_label, false_label):
        if operator == "EQ":
            self.code.append({"opcode": Opcode.JE, "operand": true_label})
        elif operator == "NEQ":
            self.code.append({"opcode": Opcode.JNE, "operand": true_label})
        elif operator == "LT":
            self.code.append({"opcode": Opcode.JB, "operand": true_label})

        else:
            raise Exception(f"Неизвестный оператор: {operator}")

        # Переход в конец блока, если условие не выполнено
        self.code.append({"opcode": Opcode.JMP, "operand": false_label})

    def generate_conditional_block(self, condition, true_label, false_label):
        # Генерация бинарной операции для условия
        left_operand_info = self.get_operand_info(condition.left)

        # Загрузка левого операнда
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": left_operand_info["value"],
                "addr_mode": left_operand_info["addr_mode"],
            }
        )

        # CMP CMP_OPERAND * (Сравнение левого операнда с правым)
        right_operand_info = self.get_operand_info(condition.right)
        self.code.append(
            {
                "opcode": Opcode.CMP,
                "operand": right_operand_info["value"],
                "addr_mode": right_operand_info["addr_mode"],
            }
        )

        # Генерация условного перехода
        self.generate_conditional_jump(condition.operator, true_label, false_label)

    def generate_string_comparison(self, node, while_loop_label, end_while_label):
        # Логика сравнения строк
        left_operand_info = self.get_operand_info(node.condition.left)
        right_operand_info = self.get_operand_info(node.condition.right)

        # LD LEFT_OPERAND * (Загружаем символ)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": left_operand_info["value"],
                "addr_mode": "indirect",
            }
        )

        # CMP CMP_SYM * (Сравнение символа)
        self.code.append(
            {
                "opcode": Opcode.CMP,
                "operand": right_operand_info["value"],
                "addr_mode": "indirect",
            }
        )

        # Условные переходы на основе оператора
        if node.condition.operator == "EQ":
            self.code.append({"opcode": Opcode.JE, "operand": while_loop_label})
        elif node.condition.operator == "NEQ":
            self.code.append({"opcode": Opcode.JNE, "operand": while_loop_label})

        # Переход в конец, если условие не выполнено
        self.code.append({"opcode": Opcode.JMP, "operand": end_while_label})

    def generate_numeric_comparison(self, node, while_loop_label, end_while_label):
        # Логика для числовых сравнений
        left_operand_info = self.get_operand_info(node.condition.left)
        right_operand_info = self.get_operand_info(node.condition.right)

        # LD LEFT_OPERAND * (Загружаем левый операнд)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": left_operand_info["value"],
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        # CMP CMP_OPERAND * (Сравнение с правым операндом)
        self.code.append(
            {
                "opcode": Opcode.CMP,
                "operand": right_operand_info["value"],
                "addr_mode": right_operand_info["addr_mode"],
            }
        )

        # Условные переходы на основе оператора
        if node.condition.operator == "LT":
            self.code.append({"opcode": Opcode.JB, "operand": while_loop_label})
        elif node.condition.operator == "EQ":
            self.code.append({"opcode": Opcode.JE, "operand": while_loop_label})
        elif node.condition.operator == "NEQ":
            self.code.append({"opcode": Opcode.JNE, "operand": while_loop_label})

        # Переход в конец, если условие не выполнено
        self.code.append({"opcode": Opcode.JMP, "operand": end_while_label})

    def generate_while(self, node):
        # Генерация меток для цикла while
        while_label_number = self.while_label_counter
        start_while_label = f"START_WHILE_{while_label_number}"
        while_loop_label = f"WHILE_LOOP_{while_label_number}"
        end_while_label = f"END_WHILE_{while_label_number}"

        # Увеличиваем счётчик меток для следующего цикла while
        self.while_label_counter += 1

        # Добавляем метки в блок меток
        self.label_block.extend(
            [
                {"label": start_while_label},
                {"label": while_loop_label},
                {"label": end_while_label},
            ]
        )

        # Сохранение метки начала цикла while
        self.code.append({"label": start_while_label})

        # Проверка типа переменной
        if isinstance(node.condition.left, StringNode) or isinstance(node.condition.right, StringNode):
            # Логика для строкового сравнения
            self.generate_string_comparison(node, while_loop_label, end_while_label)
        else:
            # Логика для числового сравнения
            self.generate_numeric_comparison(node, while_loop_label, end_while_label)

        # WHILE_LOOP:
        self.code.append({"label": while_loop_label})

        # Генерация кода для тела цикла while
        for stmt in node.body:
            if isinstance(stmt, VariableAssignNode):
                # Генерация присваивания переменной внутри цикла
                self.generate_variable_assign(stmt)
            else:
                self.generate(stmt)

        # Переход на начало цикла для повторного выполнения
        self.code.append({"opcode": Opcode.JMP, "operand": start_while_label})

        # END_WHILE:
        self.code.append({"label": end_while_label})

    def generate_if_else(self, node):
        # Генерация меток для if-else блока
        if_else_label_number = self.if_label_counter
        start_label = f"START_IF_ELSE_{if_else_label_number}"
        if_body_label = f"IF_BODY_{if_else_label_number}"
        else_body_label = f"ELSE_BODY_{if_else_label_number}"
        end_label = f"END_IF_ELSE_{if_else_label_number}"

        # Увеличиваем счётчик меток для следующего if-else блока
        self.if_label_counter += 1

        # Сохранение метки начала if-else блока
        self.code.append({"label": start_label})

        # Генерация кода для условия сравнения и переходов
        self.generate_comparison_op(node.condition, if_body_label)

        # Переход в блок else, если условие не выполнено
        self.code.append({"opcode": Opcode.JMP, "operand": else_body_label})

        # IF_BODY:
        self.code.append({"label": if_body_label})
        # Генерация кода для тела if
        for stmt in node.if_body:
            self.generate(stmt)

        # Переход к завершению if-else блока
        self.code.append({"opcode": Opcode.JMP, "operand": end_label})

        # ELSE_BODY:
        self.code.append({"label": else_body_label})
        if node.else_body:
            # Генерация кода для тела else
            for stmt in node.else_body:
                self.generate(stmt)

        # Завершаем else блок меткой конца
        self.code.append({"label": end_label})

    # Вспомогательная функция для получения операндов
    def get_operand_info(self, operand):
        if isinstance(operand, IdentifierNode):
            var_info = self.find_label(operand.value)
            if not var_info:
                raise Exception(f"Не найдена метка для переменной {operand.value}")
            return {
                "value": var_info["label"],
                "addr_mode": AddressingMode.indirect_addressing,
            }
        if isinstance(operand, NumberNode):
            return {
                "value": operand.value,
                "addr_mode": AddressingMode.immediate_addressing,
            }
        if isinstance(operand, BinaryOpNode):
            # Создание временной переменной для результата бинарной операции
            temp_var = f"TEMP_VAR_INT_{self.temp_var_int_counter}"
            data_address = len(self.data)
            self.temp_var_int_counter += 1
            self.label_block.append({"label": temp_var, "address": data_address, "type": "int"})
            self.data.append({"type": "int", "value": [0]})  # Сохраняем число в виде отдельного объекта

            self.generate_binary_op(operand, temp_var)
            return {"value": temp_var, "addr_mode": AddressingMode.indirect_addressing}
        if isinstance(operand, StringNode):
            # Если операнд строка, мы можем создать временную метку для её сравнения
            raw_string = operand.value.strip('"')
            str_label = f"STR_ADR_{self.string_label_counter}"
            self.string_label_counter += 1
            string_address = self.get_or_create_string_label(raw_string, str_label)
            return {
                "value": string_address,
                "addr_mode": AddressingMode.indirect_addressing,
                "type": "string",
            }
        else:
            raise TypeError(f"Неизвестный тип операнда {type(operand)}")

    def generate_comparison_op(self, node, true_label):
        left_operand_info = self.get_operand_info(node.left)
        right_operand_info = self.get_operand_info(node.right)

        # LD LEFT_OPERAND * (Загружаем левый операнд)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": left_operand_info["value"],
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        # CMP RIGHT_OPERAND * (Сравнение с правым операндом)
        self.code.append(
            {
                "opcode": Opcode.CMP,
                "operand": right_operand_info["value"],
                "addr_mode": right_operand_info["addr_mode"],
            }
        )

        # Условные переходы на основе оператора
        if node.operator == "EQ":
            self.code.append({"opcode": Opcode.JE, "operand": true_label})
        elif node.operator == "NEQ":
            self.code.append({"opcode": Opcode.JNE, "operand": true_label})
        elif node.operator == "LT":
            self.code.append({"opcode": Opcode.JB, "operand": true_label})

        else:
            raise Exception(f"Неизвестный оператор сравнения: {node.operator}")

    def generate_if(self, node):
        # Генерация меток для if блока
        if_label_number = self.if_label_counter
        start_label = f"START_IF_{if_label_number}"
        if_body_label = f"IF_BODY_{if_label_number}"
        end_label = f"END_IF_{if_label_number}"

        # Увеличиваем счётчик меток для следующего if блока
        self.if_label_counter += 1

        # Сохранение метки начала if блока
        self.code.append({"label": start_label})

        # Генерация кода для условия сравнения
        self.generate_comparison_op(node.condition, if_body_label)

        # Переход к метке окончания if, если условие не выполнено
        self.code.append({"opcode": Opcode.JMP, "operand": end_label})

        # IF_BODY:
        self.code.append({"label": if_body_label})
        # Генерация кода для тела if
        for stmt in node.body:
            self.generate(stmt)

        # END_IF:
        self.code.append({"label": end_label})

    def generate_label_block(self, label_type, label_counter):
        start_label = f"START_{label_type}_{label_counter}"
        end_label = f"END_{label_type}_{label_counter}"

        # Добавляем метки в блок меток
        self.label_block.append({"label": start_label})
        self.label_block.append({"label": end_label})

        # Сохранение метки начала операции
        self.code.append({"label": start_label})

        # Возвращаем конечную метку для дальнейшего использования
        return end_label

    def generate_binary_op(self, node, result_var):
        # Генерация меток для бинарной операции
        binary_op_label_number = self.binary_op_label_counter
        start_label = f"START_BINARY_OP_{binary_op_label_number}"
        end_label = f"END_BINARY_OP_{binary_op_label_number}"

        # Добавляем метки в блок меток только для стартовых и конечных меток бинарной операции
        self.label_block.append({"label": start_label})
        self.label_block.append({"label": end_label})

        # Увеличиваем счётчик меток для следующей операции
        self.binary_op_label_counter += 1

        # Сохранение метки начала операции
        self.code.append({"label": start_label})

        # Загрузка левого операнда
        left_operand_info = self.get_operand_info(node.left)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": left_operand_info["value"],
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        # Определение правого операнда
        right_operand_info = self.get_operand_info(node.right)

        # Выполнение соответствующей операции
        if node.operator == "PLUS":
            self.code.append(
                {
                    "opcode": Opcode.ADD,
                    "operand": right_operand_info["value"],
                    "addr_mode": right_operand_info["addr_mode"],
                }
            )
        elif node.operator == "MINUS":
            self.code.append(
                {
                    "opcode": Opcode.SUB,
                    "operand": right_operand_info["value"],
                    "addr_mode": AddressingMode.indirect_addressing,
                }
            )
        elif node.operator == "MUL":
            self.code.append(
                {
                    "opcode": Opcode.MUL,
                    "operand": right_operand_info["value"],
                    "addr_mode": AddressingMode.indirect_addressing,
                }
            )
        elif node.operator == "DIV":
            self.code.append(
                {
                    "opcode": Opcode.DIV,
                    "operand": right_operand_info["value"],
                    "addr_mode": AddressingMode.indirect_addressing,
                }
            )
        elif node.operator == "MOD":  # Поддержка оператора MOD
            self.code.append(
                {
                    "opcode": Opcode.MOD,
                    "operand": right_operand_info["value"],
                    "addr_mode": right_operand_info["addr_mode"],
                }
            )
        else:
            raise Exception(f"Неизвестный оператор: {node.operator}")

        # Сохранение результата в переменную result_var
        result_info = self.find_label(result_var)
        if not result_info:
            # Создаём метку, если она не была создана
            self.label_block.append({"label": result_var, "type": "int"})
            result_info = self.find_label(result_var)

        self.code.append(
            {
                "opcode": Opcode.ST,
                "operand": result_info["label"],
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        # Завершение операции
        self.code.append({"label": end_label})

    def generate_function_call(self, node):
        if node.func_name == "input":
            self.generate_input()

    def store_address_in_cur(self, str_label):
        # LD STR_ADR * (Загружаем адрес первого символа строки в AC)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": str_label,
                "addr_mode": AddressingMode.direct_addressing,
            }
        )

        # ST CUR_ADR * (Сохраняем в CUR_ADR для дальнейшей работы)
        self.code.append(
            {
                "opcode": Opcode.ST,
                "operand": "CUR_ADR",
                "addr_mode": AddressingMode.direct_addressing,
            }
        )

    def load_input_and_compare(self, end_label, cmp_char, loop_label):
        # LD IN_ADR ** (Загружаем значение из ячейки для ввода)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": "IN_ADR",
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        # CMP cmp_char # (Сравниваем значение с символом)
        self.code.append(
            {
                "opcode": Opcode.CMP,
                "operand": cmp_char,
                "addr_mode": AddressingMode.immediate_addressing,
            }
        )

        # JE END_INPUT (Если символ совпадает, переходим к метке END_INPUT)
        self.code.append({"opcode": Opcode.JE, "operand": end_label})

        # ST CUR_ADR ** (Записываем символ по текущему адресу строки)
        self.code.append(
            {
                "opcode": Opcode.ST,
                "operand": "CUR_ADR",
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        self.load_char_and_increment(loop_label)

    def load_char_and_compare(self, end_label, loop_label):
        # LD CUR_ADR ** (Загружаем символ по текущему адресу в AC)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": "CUR_ADR",
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        # CMP \0 # (Сравниваем с нуль-терминатором)
        self.code.append(
            {
                "opcode": Opcode.CMP,
                "operand": "\0",
                "addr_mode": AddressingMode.immediate_addressing,
            }
        )

        # JE END_PRINT (Если символ нуль-терминатор, переходим к метке окончания)
        self.code.append({"opcode": Opcode.JE, "operand": end_label})

        # ST OUT_ADР ** (Записываем символ в OUT_ADR)
        self.code.append(
            {
                "opcode": Opcode.ST,
                "operand": "OUT_ADR",
                "addr_mode": AddressingMode.direct_addressing,
            }
        )

        self.load_char_and_increment(loop_label)

    def load_char_and_increment(self, loop_label):
        # LD CUR_ADR * (Загружаем текущий адрес строки)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": "CUR_ADR",
                "addr_mode": AddressingMode.direct_addressing,
            }
        )

        # INC (Инкрементируем значение адреса)
        self.code.append({"opcode": Opcode.INC})

        # ST CUR_ADR * (Перезаписываем CUR_ADR новым значением)
        self.code.append(
            {
                "opcode": Opcode.ST,
                "operand": "CUR_ADR",
                "addr_mode": AddressingMode.direct_addressing,
            }
        )

        # JMP PRINT_LOOP_X или INPUT_LOOP_X (Переход к началу цикла)
        self.code.append({"opcode": Opcode.JMP, "operand": loop_label})

    def generate_int_input(self):
        input_label_number = self.input_label_counter
        start_input_label = f"START_INT_INPUT_{input_label_number}"
        end_input_label = f"END_INT_INPUT_{input_label_number}"
        int_label = f"INP_INT_ADR_{self.int_label_counter}"

        self.int_label_counter += 1
        self.label_block.extend([{"label": start_input_label}, {"label": end_input_label}])

        self.input_label_counter += 1

        int_address = len(self.data)
        self.data.append({"type": "int", "value": []})

        self.label_block.append({"label": int_label, "address": int_address, "value": "", "type": "int"})

        self.code.append({"label": start_input_label})
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": "IN_ADR",
                "addr_mode": AddressingMode.direct_addressing,
            }
        )
        self.code.append(
            {
                "opcode": Opcode.ST,
                "operand": int_label,
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        self.code.append({"label": end_input_label})

    def generate_input(self, var_name):
        input_label_number = self.input_label_counter
        start_input_label = f"START_INPUT_{input_label_number}"
        input_loop_label = f"INPUT_LOOP_{input_label_number}"
        end_input_label = f"END_INPUT_{input_label_number}"
        if var_name is None:
            var_name = f"INP_STR_ADR_{input_label_number}"

        self.input_label_counter += 1

        self.code.append({"label": start_input_label})
        self.store_address_in_cur(var_name)

        self.code.append({"label": input_loop_label})
        self.load_input_and_compare(end_input_label, ".", input_loop_label)

        self.code.append({"label": end_input_label})

    def generate_print(self, node):
        # Генерация меток для печати
        end_label = self.generate_label_block("PRINT", self.print_label_counter)

        # Увеличиваем счётчик меток для следующей печати
        self.print_label_counter += 1

        # Печать переменной
        if isinstance(node, IdentifierNode):
            var_name = node.value
            var_info = self.find_label(var_name)

            if not var_info:
                raise Exception(f"Не найдена метка для переменной {var_name}")

            if var_info["type"] == "string":
                # Генерация печати строки с PRINT_LOOP
                loop_label = f"PRINT_LOOP_{self.print_label_counter}"
                self.label_block.append({"label": loop_label})
                self.generate_string_print(var_name, loop_label, end_label)
            elif var_info["type"] == "int":
                # Печать числа, без необходимости в PRINT_LOOP
                self.generate_int_print(var_info["label"])

        # Печать числа
        elif isinstance(node, NumberNode):
            num_address = len(self.data)
            self.data.append({"type": "int", "value": node.value})
            self.generate_int_print(num_address)

        # Печать строки
        elif isinstance(node, StringNode):
            raw_string = node.value.strip('"')
            # Синхронизируем нумерацию STR_ADR с START_PRINT
            str_label = f"STR_ADR_{self.string_label_counter}"  # Используем тот же номер, что и у START_PRINT
            self.string_label_counter += 1
            loop_label = f"PRINT_LOOP_{self.print_label_counter - 1}"  # Также используем тот же номер для PRINT_LOOP
            self.label_block.append({"label": loop_label})

            # Получаем или создаём строковый адрес для печати
            string_address = self.get_or_create_string_label(raw_string, str_label)
            self.generate_string_print(string_address, loop_label, end_label)

        # Завершаем меткой окончания печати
        self.code.append({"label": end_label})

    def find_label(self, var_name):
        # Функция поиска метки переменной по имени
        for label in self.label_block:
            if label["label"] == var_name:
                return label
        return None

    def get_or_create_string_label(self, raw_string, str_label):
        # Проверка на существующую метку строки или создание новой
        for label in self.label_block:
            if label.get("value") == raw_string:
                return label["label"]  # Возвращаем строковую метку, если она уже существует

        string_address = len(self.data)
        self.data.append({"type": "string", "value": [char for char in raw_string] + ["\0"]})

        # Сохраняем строковую метку для строки
        self.label_block.append(
            {
                "label": str_label,  # Строковая метка
                "address": string_address,  # Числовой адрес в памяти данных
                "value": raw_string,  # Сохраняем значение строки
                "type": "string",
            }
        )

        return str_label  # Возвращаем строковую метку

    def generate_string_print(self, str_label, loop_label, end_label):
        self.store_address_in_cur(str_label)

        self.code.append({"label": loop_label})
        self.load_char_and_compare(end_label, loop_label)

    def generate_int_print(self, num_address):
        # LD INT (Загружаем значение целого числа в AC)
        self.code.append(
            {
                "opcode": Opcode.LD,
                "operand": num_address,  # Используем адрес числа
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

        # ST OUT_ADR ** (Записываем значение числа в OUT_ADR)
        self.code.append(
            {
                "opcode": Opcode.ST,
                "operand": "OUT_ADR",
                "addr_mode": AddressingMode.indirect_addressing,
            }
        )

    def generate_variable_assign(self, node):
        # Проверка на существование переменной
        var_info = self.find_label(node.var_name)
        var_type = node.var_type

        # Если тип переменной "unknown", пытаемся найти его из ранее созданной переменной
        if var_type == "unknown" and var_info:
            var_type = var_info.get("type", "unknown")

        if isinstance(node.expression, BinaryOpNode):
            if not var_info:
                self.label_block.append(
                    {
                        "label": node.var_name,  # Метка для переменной
                        "address": len(self.data),  # Адрес в секции данных
                        "type": "int",  # Пока предполагаем, что результат будет числом
                    }
                )
                self.data.append({"type": "int", "value": 0})  # Инициализируем значение переменной как 0

            # Выполняем бинарную операцию и сохраняем результат в переменную
            self.generate_binary_op(node.expression, node.var_name)

        elif isinstance(node.expression, FunctionCallNode):
            if node.expression.func_name == "input":
                if var_type == "STRING_TYPE" or var_type == "string":
                    # Если переменная уже существует, переиспользуем её
                    if not var_info:
                        self.string_label_counter += 1
                        data_address = len(self.data)
                        self.data.append({"type": "string", "value": [""] * 15 + ["\0"]})

                        # Создаём метку для переменной
                        self.label_block.append(
                            {
                                "label": node.var_name,
                                "address": data_address,
                                "type": "string",
                            }
                        )
                    else:
                        # Переиспользуем существующий адрес
                        data_address = var_info["address"]

                        # Затираем оставшиеся символы предыдущей строки
                        old_string_length = len(self.data[data_address]["value"])
                        new_string_length = 15
                        if old_string_length > new_string_length:
                            # Очищаем старые данные
                            self.data[data_address]["value"] = [""] * new_string_length + ["\0"]

                    self.generate_input(node.var_name)

                elif var_type == "INT":
                    self.generate_int_input()
                    if not var_info:
                        data_address = len(self.data)
                        self.data.append({"type": "int", "value": [0]})

                        self.label_block.append(
                            {
                                "label": node.var_name,
                                "address": data_address,
                                "type": "int",
                            }
                        )
                        # logging.info(f"Создание новой целочисленной переменной: {node.var_name}, адрес: {
                        # data_address}")

        elif isinstance(node.expression, NumberNode):
            # Обновляем существующую переменную или создаём новую
            if not var_info:
                data_address = len(self.data)
                self.data.append({"type": "int", "value": node.expression.value})
                self.label_block.append({"label": node.var_name, "address": data_address, "type": "int"})
                # logging.info(
                #     f"Создание новой целочисленной переменной: {node.var_name}, значение: {node.expression.value}")
            else:
                data_address = var_info["address"]
                self.data[data_address] = {
                    "type": "int",
                    "value": node.expression.value,
                }  # Обновляем значение
                # logging.info(
                #     f"Переприсваивание целочисленной переменной: {node.var_name}
                #     , новое значение: {node.expression.value}")

        elif isinstance(node.expression, StringNode):
            # Обновляем существующую строковую переменную или создаём новую
            raw_string = node.expression.value.strip('"')
            if not var_info:
                string_address = len(self.data)
                self.data.append({"type": "string", "value": [char for char in raw_string] + ["\0"]})
                self.label_block.append(
                    {
                        "label": node.var_name,
                        "address": string_address,
                        "type": "string",
                    }
                )
            else:
                string_address = var_info["address"]
                old_string_length = len(self.data[string_address]["value"])
                new_string_length = len(raw_string)

                if old_string_length > new_string_length:
                    self.data[string_address] = {
                        "type": "string",
                        "value": [char for char in raw_string]
                        + ["\0"]
                        + [""] * (old_string_length - new_string_length - 1),
                    }
                else:
                    self.data[string_address] = {
                        "type": "string",
                        "value": [char for char in raw_string] + ["\0"],
                    }

        else:
            if var_info:
                self.generate_binary_op(node.expression, node.var_name)
            else:
                raise Exception(f"Переменная {node.var_name} не найдена для присваивания.")

    def save_to_file(self, file_path="output_code.json"):
        """
        Сохраняет сгенерированный код в указанный JSON файл.
        """
        code_output = {
            "labels": self.label_block,
            "program_code": self.code,
            "data_section": self.data,
        }

        with open(file_path, "w", encoding="utf-8") as code_file:
            json.dump(code_output, code_file, ensure_ascii=False, indent=4)
