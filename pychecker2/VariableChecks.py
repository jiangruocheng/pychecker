from pychecker2.Check import Check
from pychecker2.Options import Opt, BoolOpt
from pychecker2.Warning import Warning
from pychecker2.util import parents, BaseVisitor
from pychecker2 import symbols

from compiler import ast, walk

def _is_method(scope):
    return scope.__class__ is symbols.FunctionScope and \
           scope.parent.__class__ is symbols.ClassScope

def _is_self(scope, name):
    return _is_method(scope) and name in scope.node.argnames[:1]

def is_arg_and_defaulted_to_same_name(name, scope):
    if isinstance(scope, symbols.FunctionScope):
        if name in scope.node.argnames and scope.node.defaults:
            # compute default args
            args = scope.node.argnames[:]
            # knock off kwargs
            if scope.node.kwargs:
                args = args[:-1]
            # knock off varags 
            if scope.node.varargs:
                args = args[:-1]
            # take the last args as the defaults
            args = args[-len(scope.node.defaults):]
            try:
                # get the corresponding default arg value
                default = scope.node.defaults[args.index(name)]
                # must be a Name node of the same name
                if isinstance(default, ast.Name) and \
                   default.name == name:
                    return 1
            except ValueError:
                pass
    return None


class ShadowCheck(Check):
    """Use symbol information to check that no scope defines a name
    already known to a parent scope"""

    defineNone = Warning('Report any redefinition of None',
                         'Do not redefine None')
    shadowBuiltins = Warning('Report names that shadow builtins',
                            'Identifier (%s) shadows builtin', 0)
    shadowIdentifier = Warning('Report names already defined in outer scopes',
                               'Identifier (%s) shadows definition in scope %s')
    def check(self, file, unused_checker):
        # warn if any name defined in a scope is defined in a parent scope
        # or even the builtins
        for scope in file.scopes.values():
            # skip methods of classes
            if isinstance(scope.node, ast.Class):
                continue
            for name in scope.defs:
                if name == 'None':
                    file.warning(scope.defs[name], self.defineNone)
                    continue
                if name in scope.globals:
                    continue
                if is_arg_and_defaulted_to_same_name(name, scope):
                    continue
                if _is_self(scope, name):
                    continue
                if __builtins__.has_key(name):
                    file.warning(scope.defs[name], self.shadowBuiltins, name)
                for p in parents(scope):
                    if p.defs.has_key(name) and not isinstance(p, symbols.ClassScope):
                        file.warning(scope.defs[name], self.shadowIdentifier, name, `p`)

def _str_value(s):
    if type(s) == type(''):
        return eval(s)
    return s

class UnusedCheck(Check):
    """Use symbol information to check that no scope defines a name
    not used in this or any child scope"""

    unused = Warning('Report names not used', 'Identifier (%s) not used')

    def __init__(self):
        self.reportUnusedSelf = None
        self.unusedPrefixes = None

    def get_options(self, options):
        desc = 'Ignore unused identifiers that start with these values'
        default = ['unused', 'empty', 'dummy',
                   '__pychecker__', '__all__', '__version__', 'ignored']
        options.add(Opt(self, 'unusedPrefixes', desc, default))
        
        desc = 'Ignore unused method "self" parameter'
        options.add(BoolOpt(self, 'reportUnusedSelf', desc))

    def check(self, file, unused_checker):
        self.unusedPrefixes = _str_value(self.unusedPrefixes)

        def used(name, parent_scope):
            if parent_scope.uses.has_key(name):
                return 1
            for c in parent_scope.get_children():
                if used(name, c):
                    return 1
            return 0

        for nodes, scope in file.scopes.items():
            if isinstance(nodes, ast.Function):
                code = nodes.code.nodes
                if not code:
                    continue
                # functions which only raise exceptions are unlikely to use
                # their local variables
                if isinstance(code[0], ast.Raise):
                    continue
                # functions which do nothing are unlikely to use their
                # local variables
                if len(code) == 1 and isinstance(code[0], ast.Pass):
                    continue
                # functions which just return a constant (such as None)
                # probably won't use locals,
                if len(code) == 1 and \
                   isinstance(code[0], ast.Return) and \
                   isinstance(code[0].value, ast.Const):
                    continue
                # functions which only assert falsehood are unlikely to use
                # their local variables
                if isinstance(code[0], ast.Assert):
                    if (isinstance(code[0].test, ast.Const) and \
                        not code[0].test.value) or \
                        (isinstance(code[0].test, ast.Name) and \
                         code[0].test.name == 'None'):
                        continue
            
            # ignore names defined in a class scope
            if isinstance(scope, symbols.ClassScope):
                continue

            # ensure that every defined variable is used in some scope
            for var in scope.defs:
                # check for method self
                if not self.reportUnusedSelf and _is_self(scope, var):
                    continue

                # ignore names in the root scope which are not imported:
                # class defs, function defs, variables, etc, unless
                # they start with '_'
                if scope == file.root_scope:
                    if not scope.imports.has_key(var):
                        if not var.startswith('_'):
                            continue

                for prefix in self.unusedPrefixes:
                    if var.startswith(prefix):
                        break
                else:
                    if not used(var, scope) and not scope.globals.has_key(var):
                        file.warning(scope.defs[var], self.unused, var)

def _importedName(scope, name):
    if scope.imports.has_key(name):
        return 1
    if scope.parent:
        return _importedName(scope.parent, name)
    return None

class UnknownCheck(Check):
    """Use symbol information to check that no scope uses a name
    not defined in a parent scope"""

    unknown = Warning('Report names that are not defined',
                      'Unknown identifier: %s')

    builtins = {}
    builtins.update(__builtins__)
    builtins['__builtins__'] = __builtins__
    builtins['WindowsError'] = getattr(__builtins__, 'WindowsError', None)

    def check(self, file, unused_checker):

        # if a name used is not found in the defined variables, complain
        for scope in file.scopes.values():
            for var in scope.uses:
                if not scope.defs.has_key(var):
                    for p in parents(scope):
                        if p.defs.has_key(var):
                            break
                    else:
                        if not _importedName(scope, var):
                            if not UnknownCheck.builtins.has_key(var):
                                file.warning(scope.uses[var], self.unknown, var)

def _first_arg_defaulted(function_node):
    count = len(function_node.argnames)
    if function_node.varargs:
        count -= 1
    if function_node.kwargs:
        count -= 1
    if count > 0 and len(function_node.defaults) == count:
        return 1
    return None

class SelfCheck(Check):
    'Check for simple self parameter'
    
    selfName = Warning('Report any methods whose first argument is not self',
                       'First argument to method %s (%s) is not in %s')
    selfDefault = Warning('Report a self parameter with a default value',
                          'First argument to method %s (%s) has a default value')
    
    functionSelf = Warning('Report functions (not methods) with '
                           'arguments named "self"',
                           'Argument to function (%s) is "%s"')
    
    missingSelf = Warning('Report methods without "self"',
                          'Method %s is missing self parameter')
    
    def get_options(self, options):
        desc = 'Name of self parameter'
        default = ["self", "this", "s"]
        options.add(Opt(self, 'selfNames', desc, default))

        desc = 'Suspicious self parameters'
        self.selfSuspicious = ["self"]
        options.add(Opt(self, 'selfSuspicious', desc, self.selfSuspicious))

    def check(self, file, unused_checker):
        self.selfNames      = _str_value(self.selfNames)
        self.selfSuspicious = _str_value(self.selfSuspicious)

        for scope in file.scopes.values():
            if isinstance(scope, symbols.FunctionScope):
                argnames = scope.node.argnames
                name = getattr(scope.node, 'name', 'lambda')
                if _is_method(scope):
                    if not argnames:
                        file.warning(scope.node, self.missingSelf, name)
                    if len(argnames) > 0 and argnames[0] not in self.selfNames:
                        file.warning(scope.node, self.selfName,
                                     name, argnames[0], `self.selfNames`)
                    if _first_arg_defaulted(scope.node):
                        file.warning(scope.node, self.selfDefault,
                                     name, argnames[0])
                else:
                    for arg in argnames:
                        if arg in self.selfSuspicious:
                            file.warning(scope.defs[arg], self.functionSelf,
                                         name, arg)

                

class UnpackCheck(Check):
    'Mark all unpacked variables as used'

    def __init__(self):
        self.unpackedUsed = None

    def get_options(self, options):
        desc = 'Do not treat variables used in tuple assignment as used'
        options.add(BoolOpt(self, 'unpackedUsed', desc, 1))

    def check(self, file, unused_checker):
        if not self.unpackedUsed:
            return

        class Visitor:
            def visitAssTuple(self, node):
                for c in node.getChildNodes():
                    n = node
                    while n:
                        try:
                            file.scopes[n].uses[c.name] = node.lineno
                            break
                        except (AttributeError, KeyError):
                            pass
                        n = n.parent
            visitAssList = visitAssTuple

        # local args unpacked on the `def' line are used, too
        for scope in file.scopes.values():
            if isinstance(scope.node, ast.Function):
                for arg in scope.node.argnames:
                    if isinstance(arg, tuple):
                        for unpacked in ast.flatten(arg):
                            scope.uses[unpacked] = scope.uses.get(unpacked,
                                                                  scope.node)

        if file.root_scope:
            walk(file.root_scope.node, Visitor())

def intersect2(a, b):
    return [i for i in a if i in b]

def intersect(items):
    result = items[0]
    for item in items[1:]:
        result = intersect2(result, item)
    return result

class UsedBeforeSetCheck(Check):

    usedBeforeDefined = \
          Warning('Report variables that may be used before they are defined',
                  'The local %s may be used before defined')

    def check(self, file, unused_checker):
        class Visitor(BaseVisitor):
            def __init__(self, defines = None, uses = None):
                # list of vars defined
                self.defines = []
                # name->node vars used before defined                    
                self.uses = {}
                if defines is not None:
                    self.defines = defines[:]
                if uses is not None:
                    self.uses = uses.copy()
            def visitFunction(self, node):
                self.defines.append(node.name)
            visitClass = visitFunction
            visitAssName = visitFunction
            def visitName(self, node):
                if node.name not in self.defines:
                    self.uses[node.name] = self.uses.get(node.name, node)
            def visitIf(self, node):
                if not node.else_:
                    return
                visits = []
                for test, code in node.tests:
                    visits.append(walk(code, Visitor(self.defines, self.uses)))
                visits.append(walk(node.else_,
                                   Visitor(self.defines, self.uses)))
                # compute the intersection of defines
                self.defines = intersect([v.defines for v in visits])
                # compute the union of uses, perserving first occurances
                union = {}
                visits.reverse()
                for v in visits:
                    union.update(v.uses)
                union.update(self.uses)
                self.uses = union
                        
        for scope in file.scopes.values():
            if isinstance(scope.node, ast.Function):
                params = ast.flatten(scope.params)
                for name, n in walk(scope.node.code, Visitor()).uses.items():
                    if scope.defs.has_key(name) and \
                       name not in params and \
                       not scope.imports.has_key(name):
                        file.warning(n, self.usedBeforeDefined, name)
