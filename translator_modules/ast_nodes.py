class ASTNode:
    """Базовый класс для всех узлов AST"""

    pass


class ProgramNode(ASTNode):
    """Корневой узел программы"""

    def __init__(self, statements):
        self.statements = statements


class PrintNode(ASTNode):
    """Узел для выражений print"""

    def __init__(self, expression):
        self.expression = expression


class VariableAssignNode(ASTNode):
    """Узел для присваивания переменной"""

    def __init__(self, var_name, expression, var_type):
        self.var_name = var_name
        self.expression = expression
        self.var_type = var_type


class BinaryOpNode(ASTNode):
    """Узел для бинарных операций"""

    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class NumberNode(ASTNode):
    """Узел для чисел"""

    def __init__(self, value):
        self.value = value


class StringNode(ASTNode):
    """Узел для строк"""

    def __init__(self, value):
        self.value = value


class IdentifierNode(ASTNode):
    """Узел для идентификаторов"""

    def __init__(self, value):
        self.value = value


class WhileNode(ASTNode):
    """Узел для цикла while"""

    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class IfNode(ASTNode):
    """Узел для условного оператора if"""

    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class IfElseNode(ASTNode):
    """Узел для условного оператора if-else"""

    def __init__(self, condition, if_body, else_body):
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body


class FunctionCallNode(ASTNode):
    def __init__(self, func_name):
        self.func_name = func_name
