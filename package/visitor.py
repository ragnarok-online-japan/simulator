from lark import ParseTree

class Visitor():
    def __default__(self, tree: ParseTree, env):
        raise

    def visit(self, tree: ParseTree, env):
        f = getattr(self, tree.data, self.__default__)
        return f(tree, env)

    def file_input(self, tree: ParseTree, env):
        for sub_tree in tree.children:
            r = self.visit(sub_tree, env)
            if sub_tree.data == "return":
                return r

    def assign_stmt(self, tree: ParseTree, env):
        return self.visit(tree.children[0], env)

    def assign(self, tree: ParseTree, env):
        name = self.visit(tree.children[0], env)
        value = self.visit(tree.children[1], env)
        env.set(name, value)

    def return_stmt(self, tree: ParseTree, env):
        return self.visit(tree.children[0], env)

    def funcdef(self, tree: ParseTree, env):
        key = self.visit(tree.children[0], env)
        parameters = []
        if len(tree.children) > 2:
            parameters = [self.visit(child, env) for child in tree.children[1:-1] ]
        ast = tree.children[-1]

        func = function.Function(parameters, ast)
        env.set(key, func)


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
