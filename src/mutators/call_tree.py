
from collections import defaultdict

ast = None

def get_tree_chars(depth):
    if depth <= 0:
        return ''

    split = '├'
    line = '─'
    return ' %s%s ' % (split, line * depth)

def print_call_tree_internal(func_def, depth=0, max_depth=-1):
    func_name = func_def.get('name', '<unknown func>')
    if func_name == '':
        func_name = '<constructor>'

    if func_def['nodeType'] == 'ContractDefinition':
        # calls to interface / abstract point to their contract def instead
        contract_def = func_def
    else:
        contract_def = ast.first_parent(func_def, 'ContractDefinition')

    if contract_def:
        contract_name = contract_def.get('name', '<unknown contract>')
    else:
        contract_name = '<floating>'

    print('%s%s.%s' % (get_tree_chars(depth), contract_name, func_name))

    def print_calls(node, parent):
        if node['nodeType'] != 'FunctionCall':
            return
        
        expression = node['expression']
        ref_id = expression.get('referencedDeclaration')
        if ref_id not in ast.by_id:
            return
    
        func_def = ast.by_id[ref_id]
        if func_def['nodeType'] == 'EventDefinition':
            return

        print_call_tree_internal(func_def, depth + 1)

    ast.walk_tree(func_def, callback=print_calls)

# TODO: support contract_name and method_name filtering
def print_call_tree(_ast, contract_name=None, method_name=None):
    global ast
    ast = _ast

    for func_def in ast.by_type['FunctionDefinition']:
        if method_name and func_def['name'] != method_name:
            continue

        if contract_name:
            parent = ast.first_parent(func_def, 'ContractDefinition')
            if not parent or parent.get('name', '') != contract_name:
                continue

        print_call_tree_internal(func_def, 1)
        print()

    