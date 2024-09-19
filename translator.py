import argparse
import logging

from machine_modules.memory_configurator import MemoryConfigurator
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
from translator_modules.code_generator import CodeGenerator
from translator_modules.compiler import Compiler
from translator_modules.lexer import lex
from translator_modules.parser import Parser

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)


def translate_code(
    source_code,
    ast_output_file="ast_output.txt",
    input_json_file="output_compiler.json",
    output_json_file="output_compiler_memory.json",
    instructions_file="output_instructions.json",
):
    """
    Функция для трансляции исходного кода.
    Принимает исходный код и пути к файлам JSON для промежуточных данных.
    Возвращает машинный код и AST.
    """
    logging.debug("Starting translation process.")

    # Запуск лексера
    tokens = lex(source_code)
    logging.debug("Lexer finished.")

    # Запуск парсера
    parser = Parser(tokens)
    ast = parser.parse()
    logging.debug("Parser finished. AST generated.")

    # Сохранение AST для отладки
    save_ast_to_file(ast, ast_output_file)
    logging.debug(f"AST saved to {ast_output_file}.")

    # Генерация кода
    generator = CodeGenerator()
    generator.generate(ast)
    generator.save_to_file()
    logging.debug("Code generation finished.")

    # Компиляция
    compiler = Compiler("output_code.json")
    compiler.save_unified_json(input_json_file)
    logging.debug(f"Unified JSON saved to {input_json_file}.")

    # Настройка памяти
    configurator = MemoryConfigurator(input_json_file)
    configurator.save_data_to_json(output_json_file)
    configurator.save_instructions_to_json(instructions_file)
    logging.debug(f"Memory configuration saved to {output_json_file} and {instructions_file}.")

    # Возврат сгенерированных данных для тестирования
    with open(output_json_file, encoding="utf-8") as f:
        machine_code = f.read()

    logging.debug("Translation process completed.")

    return ast, machine_code


def save_ast_to_file(node, filename):
    """Сохраняет AST в файл"""
    ast_output = []

    def print_ast(ast_node, indent=""):
        """Функция для сохранения AST в список"""
        if isinstance(ast_node, ProgramNode):
            ast_output.append(indent + "Program:")
            for stmt in ast_node.statements:
                print_ast(stmt, indent + "  ")
        elif isinstance(ast_node, PrintNode):
            ast_output.append(indent + "Print:")
            print_ast(ast_node.expression, indent + "  ")
        elif isinstance(ast_node, VariableAssignNode):
            ast_output.append(indent + f"Assign(var={ast_node.var_name}, var_type={ast_node.var_type})")
            print_ast(ast_node.expression, indent + "  ")
        elif isinstance(ast_node, WhileNode):
            ast_output.append(indent + "While:")
            ast_output.append(indent + "  Condition:")
            print_ast(ast_node.condition, indent + "    ")
            ast_output.append(indent + "  WhileBody:")
            for stmt in ast_node.body:
                print_ast(stmt, indent + "    ")
        elif isinstance(ast_node, IfNode):
            ast_output.append(indent + "If:")
            ast_output.append(indent + "  Condition:")
            print_ast(ast_node.condition, indent + "    ")
            ast_output.append(indent + "  Body:")
            for stmt in ast_node.body:
                print_ast(stmt, indent + "    ")
        elif isinstance(ast_node, IfElseNode):
            ast_output.append(indent + "IfElse:")
            ast_output.append(indent + "  Condition:")
            print_ast(ast_node.condition, indent + "    ")
            ast_output.append(indent + "  IfBody:")
            for stmt in ast_node.if_body:
                print_ast(stmt, indent + "    ")
            ast_output.append(indent + "  ElseBody:")
            for stmt in ast_node.else_body:
                print_ast(stmt, indent + "    ")
        elif isinstance(ast_node, BinaryOpNode):
            ast_output.append(indent + "BinaryOp(")
            print_ast(ast_node.left, indent + "    ")
            ast_output.append(indent + f"  {ast_node.operator}")
            print_ast(ast_node.right, indent + "    ")
            ast_output.append(indent + ")")
        elif isinstance(ast_node, NumberNode):
            ast_output.append(f"{indent}Number({ast_node.value})")
        elif isinstance(ast_node, StringNode):
            ast_output.append(f"{indent}String({ast_node.value})")
        elif isinstance(ast_node, IdentifierNode):
            ast_output.append(f"{indent}Identifier({ast_node.value})")
        elif isinstance(ast_node, FunctionCallNode):
            ast_output.append(f"{indent}FunctionCall({ast_node.func_name})")

    print_ast(node)

    with open(filename, "w", encoding="utf-8") as file:
        for line in ast_output:
            file.write(line + "\n")


def parse_arguments():
    """Функция для обработки аргументов командной строки."""
    parser = argparse.ArgumentParser(description="Translate and execute code.")

    parser.add_argument("input_file", type=str, help="Path to the input source code file.")

    parser.add_argument(
        "target_file",
        type=str,
        help="Path to the target output file (for machine code or instructions).",
    )

    return parser.parse_args()


def main():
    """Основная функция для работы с командной строкой."""
    # Инициализация парсера аргументов
    parser = argparse.ArgumentParser(description="Translate and execute code.")
    parser.add_argument("input_file", help="Input source file to be translated.")
    parser.add_argument("target_file", help="Target file to store the result.")

    args = parse_arguments()

    # Чтение исходного кода из файла
    with open(args.input_file, encoding="utf-8") as file:
        source_code = file.read()

    logging.debug(f"Source code read from {args.input_file}")

    # Запуск трансляции исходного кода
    ast, machine_code = translate_code(
        source_code,
        ast_output_file="output_code.json",
        input_json_file="output_compiler.json",
        output_json_file="output_compiler_memory.json",
        instructions_file=args.target_file,
    )

    logging.debug(f"Translation completed and output saved to {args.target_file}")


if __name__ == "__main__":
    main()
