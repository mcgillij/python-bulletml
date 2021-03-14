"""BulletML expression evaluator.

http://www.asahi-net.or.jp/~cs8k-cyu/bulletml/index_e.html
"""

# BulletML assumes 1/2 = 0.5.
from __future__ import division

import random
import re

from bulletml.errors import Error

__all__ = ["ExprError", "NumberDef", "INumberDef"]

class ExprError(Error):
    """Raised when an invalid expression is evaluated/compiled."""
    pass

class NumberDef(object):
    """BulletML numeric expression.

    This translates BulletML numeric expressions into Python expressions.

    Examples:
    35
    360/16
    0.7 + 0.9*$rand
    180-$rank*20
    (2+$1)*0.3

    """

    GLOBALS = dict(random=random.random, __builtins__={})

    def __init__(self, expr):
        try:
            expr = expr.string
        except AttributeError:
            pass
        try:
            if "__" in expr:
                # nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
                raise ExprError(expr)
        except TypeError:
            pass
        self.string = expr = str(expr)
        repl = lambda match: "params[%d]" % (int(match.group()[1:]) - 1)
        expr = re.sub(r"\$\d+", repl, expr.lower())
        self.__expr = expr.replace("$rand", "random()").replace("$rank", "rank")
        try:
            try:
                self._value = eval(self.__expr, dict(__builtins__={}))
            except NameError:
                variables = dict(rank=1, params=[0] * 99)
                value = eval(self.__expr, self.GLOBALS, variables)
                if not isinstance(value, (int, float)):
                    raise TypeError(expr)
                self._value = None
                self.expr = self.string
            else:
                self.expr = self._value
        except Exception:
            raise ExprError(expr)
        self.__expr = compile(self.__expr, __file__, "eval")

    def __call__(self, params, rank):
        """Evaluate the expression and return its value."""
        if self._value is not None:
            return self._value
        variables = { 'rank': rank, 'params': params }
        return eval(self.__expr, self.GLOBALS, variables)

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.expr)

class INumberDef(NumberDef):
    """A NumberDef, but returns rounded integer results."""
    def __init__(self, expr):
        super(INumberDef, self).__init__(expr)
        if self._value is not None:
            self._value = int(round(self._value))

    def __call__(self, params, rank):
        # Avoid int(round(__call__())) overhead for constants.
        if self._value is not None:
            return self._value
        return int(round(super(INumberDef, self).__call__(params, rank)))
