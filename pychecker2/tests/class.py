import compiler
import compiler                                          as one
import compiler.ast
import compiler.ast                                      as two
# import compiler.ast.Const
# import compiler.ast.Const                                as three
from   compiler import ast
from   compiler import ast                               as four
from   compiler.ast import Const
from   compiler.ast import Const                         as five

func = lambda x: x

class D:
    class B(compiler.ast.Const):
        inherited2 = 1
        def x(self):
            self.inherited1 = 1

class A(D.B):
    def __init__(self):
        self.x = 1                      # define x on A
        self.w.q = 1

    def f(s, self):                     # unusual self
        print self
        s.self = 1
        s = 7

    def x():                            # no self, redefine x on object
        pass

    def y(self):
        self.a, self.b = (1, 2)         # define a, b

    def _z(self):
        print self._z                   # method
        print self.x                    # assigned
        print self.a                    # unpacked
        print self.w                    # unknown
        print self.inherited1           # known from B
        print self.inherited2           # known from B
        print self.value                # from compiler.ast.Const, fails
        print self.goofy                # defined in class scope

    goofy = x
    
class E(one.ast.Const):
    def f(self):
        print self.value                # fails

class F(two.Const):
    def f(self):
        print self.value

class H(four.Const):
    def f(self):
        print self.value                # fails

class I(five):
    def f(self):
        print self.value

class J(ast.Const):
    def f(self):
        print self.value                # fails

class K(Const):
    def f(self):
        print self.value
