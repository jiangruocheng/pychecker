
from pychecker2.Check import Check
from pychecker2.Check import Warning
from pychecker2.util import ScopeVisitor

from compiler import walk

class ImportCheck(Check):
    '''
Get 'from module import *' names hauled into the file and modules.
Figure out which names come from 'import name'.
    '''

    importError = Warning('Report/ignore imports that may fail',
                          'Error trying to import %s: %s')
    duplicateImport = Warning('Report/ignore duplicate imports',
                              'Import of "%s" is duplicate%s')
    shadowImport = Warning('Report imports which shadow names from other imports',
                              'Import of "%s" duplicates import from module %s at %d')

    def check(self, unused_modules, file, unused_options):
        def try_import(name, node):
            try:
                return __import__(name, globals(), {}, [''])
            except ImportError, detail:
                file.warning(node, ImportCheck.importError, name, detail)
                return None
        def add_import(scopes, node, name, module):
            for scope in scopes:
                try:
                    smodule, snode = scope.imports[name]
                    if smodule == module:
                        if scope == scopes[0]:
                            extra = " in current scope"
                        else:
                            extra = " of import in parent scope %s" % scope
                        file.warning(node, ImportCheck.duplicateImport,
                                     name, extra)
                    else:
                        file.warning(node, ImportCheck.shadowImport,
                                     name, smodule.__name__, snode.lineno)
                except KeyError:
                    pass
            scopes[0].imports[name] = (module, node)
            
        class FromImportVisitor:

            def visitFrom(self, node, *scopes):
                m = try_import(node.modname, node)
                if m:
                    for module_name, local_name in node.names:
                        if module_name == '*':
                            for name in dir(m):
                                if not name.startswith('_'):
                                   add_import(scopes, node, name, m)
                        else:
                            add_import(scopes, node,
                                       local_name or module_name, m)

            def visitImport(self, node, *scopes):
                for module, name in node.names:
                    m = try_import(module, node)
                    if m:
                        # example: os.path stored under "os" or supplied name
                        base = module.split('.')[0]
                        add_import(scopes, node, name or base, m)


        if file.root_scope:
            walk(file.root_scope.node,
                 ScopeVisitor(file.scopes, FromImportVisitor()))
