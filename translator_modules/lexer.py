import re

# Определение токенов
TOKEN_SPECIFICATION = [
    ("NEQ", r"!="),
    ("STRING_TYPE", r"string"),  # Ключевое слово string
    ("INPUT", r"input"),  # Функция input()
    ("EQ", r"=="),  # Равно
    ("INT", r"int"),  # Ключевое слово int
    ("WHILE", r"while"),  # Ключевое слово while
    ("IF", r"if"),  # Ключевое слово if
    ("ELSE", r"else"),  # Ключевое слово else
    ("PRINT", r"print"),  # Ключевое слово print
    ("NUMBER", r"\d+"),  # Число
    ("STRING", r'"[^"]*"'),  # Строковый литерал
    ("ID", r"[A-Za-z_]\w*"),  # Идентификатор
    ("PLUS", r"\+"),  # Оператор сложения
    ("MINUS", r"-"),  # Оператор вычитания
    ("MUL", r"\*"),  # Оператор умножения
    ("DIV", r"/"),  # Оператор деления
    ("MOD", r"%"),  # Оператор взятия остатка
    ("LT", r"<"),  # Меньше
    ("HT", r">"),  # Больше
    ("ASSIGN", r"="),  # Оператор присваивания
    ("LPAREN", r"\("),  # Левая круглая скобка
    ("RPAREN", r"\)"),  # Правая круглая скобка
    ("LBRACE", r"\{"),  # Левая фигурная скобка
    ("RBRACE", r"\}"),  # Правая фигурная скобка
    ("SEMI", r";"),  # Точка с запятой
    ("SKIP", r"[ \t\n]+"),  # Пробелы, табуляция и новая строка
    ("MISMATCH", r"."),  # Неизвестный символ
]

# Компиляция регулярных выражений
token_regex = "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in TOKEN_SPECIFICATION)


# Лексер
def lex(code):
    tokens = []

    for mo in re.finditer(token_regex, code):
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind == "NUMBER":
            value = int(value)
        elif kind == "ID" or kind in {"INT", "WHILE", "IF", "ELSE"}:
            value = str(value)
        elif kind == "SKIP":
            continue
        elif kind == "MISMATCH":
            raise RuntimeError(f"Неожиданный символ: {value!r}")

        tokens.append((kind, value))

    return tokens
