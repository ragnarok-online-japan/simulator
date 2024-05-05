from lark import ParseTree, lexer
from decimal import Decimal, getcontext

# 丸め誤差
getcontext().prec = 10

class Visitor():
    _env = None

    def __init__(self, env) -> None:
        self._env = env

    def __default__(self, tree: ParseTree):
        raise

    def visit(self, tree: ParseTree):
        f = getattr(self, tree.data, self.__default__)
        return f(tree)

    def file_input(self, tree: ParseTree):
        for sub_tree in tree.children:
            r = self.visit(sub_tree)
            if sub_tree.data == "return_stmt":
                return r

    def assign_stmt(self, tree: ParseTree):
        return self.visit(tree.children[0])

    def assign(self, tree: ParseTree):
        key = str(tree.children[0].children[0].children[0])
        value = self.visit(tree.children[1])
        self._env.set(key, value)

    def var(self, tree: ParseTree):
        key = self.visit(tree.children[0])
        value = self._env.get(key)
        return value

    def return_stmt(self, tree: ParseTree):
        return self.visit(tree.children[0])

    def expr_stmt(self, tree: ParseTree):
        return self.visit(tree.children[0])

    def arith_expr(self, tree: ParseTree):
        value = Decimal(0)
        action = None
        for sub_tree in tree.children:
            if isinstance(sub_tree, (lexer.Token)):
                action = str(sub_tree)
                continue

            temp_value = Decimal(self.visit(sub_tree))
            if action is None:
                value = temp_value
                continue

            if action == "+":
                value += temp_value
            elif action == "-":
                value -= temp_value
            elif action == "*":
                value *= temp_value
            elif action == "/":
                value /= temp_value
            elif action == "%":
                value %= temp_value
            action = None

        return value

    def term(self, tree: ParseTree):
        value1 = Decimal(self.visit(tree.children[0]))
        action = str(tree.children[1])
        value2 = Decimal(self.visit(tree.children[2]))

        if action == "+":
            value = value1 + value2
        elif action == "-":
            value = value1 - value2
        elif action == "*":
            value = value1 * value2
        elif action == "/":
            value = value1 / value2
        elif action == "%":
            value = value1 % value2

        return value

    def funcdef(self, tree: ParseTree):
        key = self.visit(tree.children[0])
        parameters = []
        if len(tree.children) > 2:
            parameters = [self.visit(child) for child in tree.children[1:-1]]
        ast = tree.children[-1]

        func = function.Function(parameters, ast)
        self._env.set(key, func)

    def name(self, tree: ParseTree):
        return str(tree.children[0])

    def number(self, tree: ParseTree):
        value = str(tree.children[0].value).replace(",", "")
        if value.find(".") > 0:
            return float(value)
        else:
            return int(value)

    def string(self, tree: ParseTree):
        return str(tree.children[0].value)

    def const_none(self, tree: ParseTree):
        return None

    def const_true(self, tree: ParseTree):
        return True

    def const_false(self, tree: ParseTree):
        return False

class Function():
    def __init__(self, parameters, tree):
        self._parameters = parameters
        self._tree = tree

    def parameters(self):
        return self._parameters

    def tree(self):
        return self._tree

class Environment():
    _point: dict = {}
    _env: dict = {}

    def __init__(self, point:dict = {}):
        self._point = point

    def get(self, key) -> str|int|float|None:
        value: str|int|float|None = None
        if key in self._point:
            value = self._point.get(key, None)
        else:
            value = self._env.get(key, None)
        return value

    def set(self, key, value):
        if key in self._point:
            self._point[key] = value
        else:
            self._env[key] = value
