'test abstract classes'

__pychecker__ = 'no-classdoc'

class Abstract:
    def f(self): raise SystemError("override in subclass")
    def g(self): raise KeyError("override in subclass")
class ConcreteBad(Abstract):
    def g(self): pass
class ConcreteGood(ConcreteBad):
    def f(self): pass
a = Abstract()                          # error
cb = ConcreteBad()                      # error
cg = ConcreteGood()                     # ok, f defined

cb.g()
def f():
    class MoreBad(Abstract):
        def g(): pass
    _ = MoreBad()                       # FIXME, error not caught

import import73
class ImplAbstract(import73.AbstractLib): pass

def lib_example():
    _ = import73.AbstractLib()          # error
    _ = ImplAbstract()                  # error