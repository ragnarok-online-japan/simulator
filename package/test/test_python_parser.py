#!/usr/bin/env python3
import textwrap
import unittest
import sys
sys.path.append("../")

from lark import Lark
from lark.indenter import PythonIndenter
from visitor import Visitor, Environment

class TestPythonParser(unittest.TestCase):
    def setUp(self) -> None:
        kwargs = dict(postlex=PythonIndenter(), start=["file_input"])

        rule: str = ""
        with open("../python3_like.lark", mode="r") as fp:
            rule = fp.read()

        self.python_parser = Lark(rule, parser='lalr', **kwargs)

    def calc(self, code: str):
        tree = self.python_parser.parse(code)
        #print(tree.pretty())

        env = Environment({
            "str" : 100
        })
        visitor = Visitor(env)
        return visitor.visit(tree)

    def test1(self):
        code: str = textwrap.dedent("""
        str = 1

        return str
        """)

        self.assertEqual(self.calc(code), 1)

    def test2(self):
        code: str = textwrap.dedent("""
        str = str * 1.1 + 1 - 2 * 3

        return str
        """)

        self.assertEqual(self.calc(code), 105)

    def _test3(self):
        code: str = textwrap.dedent("""
        num = 1
        if num == 1:
            num = num * 2

        if num == 1:
            num = num + 1
        else:
            num = num * 2

        return num
        """)

        self.assertEqual(self.calc(code), 4)

    def _test4(self):
        code: str = textwrap.dedent("""
        num = 2

        if num == 1:
            num = num + 1
        elif num == 2:
            num = num * 2
        endif

        return num
        """)

        self.assertEqual(self.calc(code), 4)

if __name__ == "__main__":
    unittest.main()
