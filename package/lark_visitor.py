from lark import ParseTree

class Visitor():
    def __default__(self, tree: ParseTree, env):
        raise

    def program(self, tree: ParseTree, env):
        for sub_tree in tree.children:
            r = self.visit(sub_tree, env)
            if sub_tree.data == "return_state":
                return r

    def assignment(self, tree: ParseTree, env):
        key = self.visit(tree.children[0], env)
        value = self.visit(tree.children[1], env)
        env.set(key, value)

    def return_state(self, tree: ParseTree, env):
        return self.visit(tree.children[0], env)

    def new_symbol(self, tree: ParseTree, env):
        return tree.children[0].value

    def parameter(self, tree: ParseTree, env):
        return tree.children[0].value

    def condition(self, tree: ParseTree, env):
        condition = self.visit(tree.children[0], env)

        if condition == True:
            return self.visit(tree.children[1], env)
        elif len(tree.children) > 2:
            return self.visit(tree.children[2], env)
        else:
            return None

    def eq(self, tree: ParseTree, env) -> bool:
        return bool(self.visit(tree.children[0], env) == self.visit(tree.children[1], env))

    def ne(self, tree: ParseTree, env) -> bool:
        return bool(self.visit(tree.children[0], env) != self.visit(tree.children[1], env))

    def lt(self, tree: ParseTree, env) -> bool:
        return bool(self.visit(tree.children[0], env) <  self.visit(tree.children[1], env))

    def le(self, tree: ParseTree, env) -> bool:
        return bool(self.visit(tree.children[0], env) <= self.visit(tree.children[1], env))

    def gt(self, tree: ParseTree, env) -> bool:
        return bool(self.visit(tree.children[0], env) >  self.visit(tree.children[1], env))

    def ge(self, tree: ParseTree, env) -> bool:
        return bool(self.visit(tree.children[0], env) >= self.visit(tree.children[1], env))

    def function(self, tree: ParseTree, env):
        key = self.visit(tree.children[0], env)
        parameters = []
        if len(tree.children) > 2:
            parameters = [self.visit(child, env) for child in tree.children[1:-1] ]
        ast = tree.children[-1]

        func = function.Function(parameters, ast)
        env.set(key, func)

    def function_call(self, tree: ParseTree, env):
        func = self.visit(tree.children[0], env)

        arguments = [self.visit(c, env) for c in tree.children[1:]]
        if len(arguments) != len(func.parameters()):
            raise BaseException("Number of arguments is wrong")

        local_env = Environment(env)
        for (k, v) in zip(func.parameters(), arguments):
            local_env.set(k, v)

        return self.visit(func.tree(), local_env)

    def addition(self, tree: ParseTree, env):
        left = self.visit(tree.children[0], env)
        right = self.visit(tree.children[1], env)
        return left + right

    def substraction(self, tree: ParseTree, env) -> float:
        left = self.visit(tree.children[0], env)
        right = self.visit(tree.children[1], env)
        return left - right

    def multiplication(self, tree: ParseTree, env) -> float:
        left = self.visit(tree.children[0], env)
        right = self.visit(tree.children[1], env)
        return left * right

    def divisiton(self, tree: ParseTree, env) -> float:
        left = self.visit(tree.children[0], env)
        right = self.visit(tree.children[1], env)
        return left / right

    def symbol(self, tree: ParseTree, env):
        key = tree.children[0].value
        return env.get(key)

    def number(self, tree: ParseTree, env) -> float:
        return float(tree.children[0].value)

    def visit(self, tree: ParseTree, env):
        f = getattr(self, tree.data, self.__default__)
        return f(tree, env)

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
    def __init__(self, point):
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
