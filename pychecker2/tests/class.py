import compiler
import compiler                   as one
import compiler.ast              
import compiler.ast               as two
from   compiler import ast       
from   compiler import ast        as three
from   compiler.ast import Const 
from   compiler.ast import Const  as four

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
        print self.value

class F(two.Const):
    def f(self):
        print self.value

class H(three.Const):
    def f(self):
        print self.value

class I(four):
    def f(self):
        print self.value

class J(ast.Const):
    def f(self):
        print self.value

class K(Const):
    def f(self):
        print self.value

#
# Various abusive imports, all under a non-global scope
#

def z(arg):
    from xml.dom import minidom as md

    class L(md.Node):
        def f(self):
            print arg, self.childNodes
    print L()

def zz(arg):
    from xml import dom as d

    class L(d.minidom.Node):
        def f(self):
            print arg, self.childNodes
    print L()

def zzz(arg):
    from xml.dom.minidom import Node as X

    class L(X):
        def f(self):
            print arg, self.childNodes
    print L()

def zzz(arg):
    from tests import nested

    class L(nested.N1.N2):
        def f(self):
            print self.x
    print L(), arg
