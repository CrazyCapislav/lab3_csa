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


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):
        """Парсер возвращает корневой узел программы"""
        self.eat("LBRACE")  # Ожидаем, что программа начинается с '{'
        statements = self.parse_block()
        self.eat("RBRACE")  # Ожидаем, что программа заканчивается '}'
        return ProgramNode(statements)

    def parse_block(self):
        """Парсинг блока операторов"""
        statements = []
        while self.current_token()[0] != "RBRACE":
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        return statements

    def parse_statement(self):
        """Парсинг отдельного оператора"""
        token = self.current_token()

        if token[0] == "PRINT":
            return self.parse_print()
        if token[0] == "ID":
            return self.parse_assignment()
        if token[0] in {"INT", "STRING_TYPE"}:  # Обработка объявлений int и string
            return self.parse_declaration()
        if token[0] == "WHILE":
            return self.parse_while()
        if token[0] == "IF":
            return self.parse_if()
        else:
            self.error(f"Неизвестный оператор: {token}")
            return None

    def parse_print(self):
        """Парсинг оператора print"""
        self.eat("PRINT")
        self.eat("LPAREN")
        expr = self.parse_expression()
        self.eat("RPAREN")
        self.eat("SEMI")
        return PrintNode(expr)

    def parse_while(self):
        """Парсинг оператора while"""
        self.eat("WHILE")
        self.eat("LPAREN")
        condition = self.parse_expression()  # Парсим условие цикла
        self.eat("RPAREN")
        self.eat("LBRACE")
        body = self.parse_block()  # Парсим тело цикла
        self.eat("RBRACE")
        return WhileNode(condition, body)

    def parse_if(self):
        """Парсинг оператора if"""
        self.eat("IF")
        self.eat("LPAREN")

        # Убедитесь, что парсер правильно обрабатывает выражение до RPAREN
        condition = self.parse_expression()

        self.eat("RPAREN")  # Ожидание закрывающей скобки
        self.eat("LBRACE")
        body = self.parse_block()  # Парсим тело if
        self.eat("RBRACE")

        # Проверка на наличие else
        if self.current_token()[0] == "ELSE":
            self.eat("ELSE")
            self.eat("LBRACE")
            else_body = self.parse_block()  # Парсим тело else
            self.eat("RBRACE")
            return IfElseNode(condition, body, else_body)

        return IfNode(condition, body)

    def parse_assignment(self):
        """Парсинг присваивания переменной"""
        var_name = self.current_token()[1]
        self.eat("ID")
        self.eat("ASSIGN")
        expr = self.parse_expression()
        if isinstance(expr, NumberNode):
            var_type = "int"
        elif isinstance(expr, StringNode):
            var_type = "string"
        else:
            var_type = "unknown"
        self.eat("SEMI")
        return VariableAssignNode(var_name, expr, var_type)

    def parse_declaration(self):
        """Парсинг объявления переменной"""
        if self.current_token()[0] in {"INT", "STRING_TYPE"}:  # Поддержка string
            var_type = self.current_token()[0]
            self.eat(var_type)
            var_name = self.current_token()[1]
            self.eat("ID")
            expr = None
            if self.current_token()[0] == "ASSIGN":
                self.eat("ASSIGN")
                expr = self.parse_expression()
            self.eat("SEMI")
            return VariableAssignNode(var_name, expr, var_type)
        else:
            return None

    def parse_expression(self):
        """Парсинг выражения с поддержкой бинарных операций"""
        left = self.parse_term()

        # Парсинг бинарных операций
        while self.current_token()[0] in {
            "LT",
            "HT",
            "LE",
            "HE",
            "PLUS",
            "MINUS",
            "MUL",
            "DIV",
            "EQ",
            "NEQ",
            "MOD",
            "ASSIGN",
        }:
            operator = self.current_token()[0]
            self.eat(operator)
            right = self.parse_term()
            left = BinaryOpNode(left, operator, right)

        return left

    def parse_function_call(self):
        """Парсинг вызова функции, такой как input()"""
        func_name = self.current_token()[1]
        self.eat("ID")
        self.eat("LPAREN")
        self.eat("RPAREN")
        self.eat("SEMI")
        return FunctionCallNode(func_name)

    def parse_term(self):
        """Парсинг простого терма (числа, идентификатора, строк, выражений в скобках)"""
        token = self.current_token()

        if token[0] == "NUMBER":
            self.eat("NUMBER")
            return NumberNode(token[1])
        if token[0] == "STRING":
            self.eat("STRING")
            return StringNode(token[1])
        if token[0] == "ID":
            self.eat("ID")
            return IdentifierNode(token[1])
        if token[0] == "LPAREN":
            self.eat("LPAREN")
            expr = self.parse_expression()
            self.eat("RPAREN")
            return expr
        if token[0] == "INPUT":
            self.eat("INPUT")
            self.eat("LPAREN")
            self.eat("RPAREN")
            return FunctionCallNode("input")
        else:
            return None

    def current_token(self):
        """Возвращает текущий токен"""
        return self.tokens[self.pos]

    def eat(self, token_type):
        """Проверяет текущий токен и переходит к следующему"""
        token = self.current_token()
        if token[0] == token_type:
            self.pos += 1
        else:
            self.error(f"Ожидался токен {token_type}, но найден {token[0]}")

    def error(self, message):
        raise Exception(message)
