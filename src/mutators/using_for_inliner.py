import argparse

# TODO: fix this temporary hack
ast = None

def make_identifier(name, parent_id, referencedDeclaration=-1):
    return {
        "id": ast.next_node_id(),
        "name": name,
        "nodeType": "Identifier",
        #"overloadedDeclarations": [],
        "referencedDeclaration": referencedDeclaration,
        "typeDescriptions": {
            # just to satisfy `sol-ast-compile` tool
        },
        "parent_id": parent_id
    }

# embed "using .. for .." statements BECAUSE THEY SUCK
def embed_using_for(_ast, keep_directive=False):
    global ast
    ast = _ast
    lib_funcs_to_lib_id = {}
    lib_ids = {}
    for func_def in ast.by_type.get('FunctionDefinition'):
        contract = ast.first_parent(func_def, 'ContractDefinition')
        if contract.get('contractKind') != 'library':
            continue

        lib_ids[contract['id']] = contract['name']
        lib_funcs_to_lib_id[func_def['id']] = contract['name']

    for mem_acc in ast.by_type.get('MemberAccess'):
        ref_id = mem_acc.get('referencedDeclaration')
        if ref_id not in lib_funcs_to_lib_id:
            continue

        # note: structure should be FunctionCall(MemberAccess(expression), args..)
        # and translated to FunctionCall(expression, MemberAccess(Identifier(library)) + args)
        func_call = ast.by_id[mem_acc['parent_id']]
        if func_call['nodeType'] != 'FunctionCall':
            continue

        first_arg = mem_acc['expression']
        
        # check that the accessed member isn't already the lib
        exp_ref_id = first_arg.get('referencedDeclaration')
        if exp_ref_id in lib_ids:
            continue

        # replace with a lib Identifier
        id_node = make_identifier(lib_funcs_to_lib_id[ref_id], mem_acc['parent_id'])
        mem_acc['expression'] = id_node
        func_call['arguments'] = [first_arg] + func_call['arguments']

    if not keep_directive:
        for using in ast.by_type.get('UsingForDirective'):
            ast.by_id[using['parent_id']]['nodes'].remove(using)

    return True

def run_cli(_ast, raw_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--keep-directive', default=False, action='store_true', help='inline but keep the "using .. for .." directive')
    args = parser.parse_args(raw_args)
    return embed_using_for(_ast, args.keep_directive)
