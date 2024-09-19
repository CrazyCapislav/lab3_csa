import contextlib
import io
import json
import logging
import os
import tempfile
from pathlib import Path

import pytest

from machine import ControlUnit
from machine_modules.data_path import DataPath
from machine_modules.memory_configurator import MemoryConfigurator
from translator import translate_code
from translator_modules.code_generator import CodeGenerator
from translator_modules.lexer import lex
from translator_modules.parser import Parser


@pytest.mark.golden_test("golden/*.yml")
def test_ast(golden, caplog):
    """
    Тестирует работу парсера и проверяет AST (абстрактное синтаксическое дерево)
    """
    caplog.set_level(logging.DEBUG)

    with contextlib.redirect_stdout(io.StringIO()):
        # Получаем AST из исходного кода
        translate_code(golden["in_source"], ast_output_file="ast_output.txt")

        # Читаем результат из файла ast_output.txt
        with open("ast_output.txt", encoding="utf-8") as ast_file:
            ast_output = ast_file.read()

    assert ast_output == golden.out["out_ast"]


@pytest.mark.golden_test("golden/*.yml")
def test_generator(golden, caplog):
    """
    Тестирует генерацию кода и сравнивает с ожидаемым результатом в секции out_code.
    """
    caplog.set_level(logging.DEBUG)

    tokens = lex(golden["in_source"])

    parser = Parser(tokens)
    ast = parser.parse()

    generator = CodeGenerator()
    generator.generate(ast)

    with tempfile.TemporaryDirectory() as tmpdirname:
        output_code_file = os.path.join(tmpdirname, "output_code.json")
        generator.save_to_file(output_code_file)

        with open(output_code_file, encoding="utf-8") as file:
            code_output = file.read()

    assert code_output == golden.out["out_code"], "Сгенерированный код не соответствует ожидаемому"

    logging.debug("Code generation finished.")


@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden, caplog):
    """
    Тестирует генерацию кода и выполнение программы, проверяет stdout и логи.
    """
    caplog.set_level(logging.DEBUG)

    dirname = "/tmp/fixed_test_dir"
    Path(dirname).mkdir(parents=True, exist_ok=True)

    input_json_file = os.path.join(dirname, "output_compiler.json")
    output_json_file = os.path.join(dirname, "output_compiler_memory.json")
    instructions_file = os.path.join(dirname, "output_instructions.json")

    translate_code(
        golden["in_source"],
        input_json_file=input_json_file,
        output_json_file=output_json_file,
    )

    configurator = MemoryConfigurator(input_json_file)
    configurator.save_data_to_json(output_json_file)
    configurator.save_instructions_to_json(instructions_file)

    input_buffer = list(golden["in_stdin"])

    data_path = DataPath(output_json_file, input_buffer)

    with open(instructions_file, encoding="utf-8") as file:
        program = json.load(file)["instructions"]

    control_unit = ControlUnit(program, data_path)

    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        control_unit.run()

    logs = caplog.text.replace("\u0000", "\\u0000")

    assert stdout.getvalue() == golden.out["out_stdout"], "Вывод программы не соответствует ожидаемому"
    assert logs == golden.out["out_log"], "Логи программы не соответствуют ожидаемым"
