
ast = None

def make_block(*statements):
    return {
        "id": 0,
        #"parent_id": parent_id, # TODO: pass this..
        "nodeType": "Block",
        "src": "29254:584:0",
        "statements": statements
    }

def reparent(parent_id, *nodes):
    for node in nodes:
        node['parent_id'] = parent_id,

def make_tuple(components):
    new_id = ast.next_node_id()
    return {
        "components": ast.clone(components, new_id),
        "id": new_id,
        "isConstant": False,
        "isInlineArray": False,
        "isLValue": False,
        "isPure": False,
        "lValueRequested": False,
        "nodeType": "TupleExpression",
        "typeDescriptions": {
            # just to satisfy `sol-ast-compile` tool
        }
    }

# make VariableDeclarationStatement ie. (params) = (args) from FunctionDefinition(params), FunctionCall(args)
def make_var_dec_st_from_func_call(params_decl, arg_values):
    new_id = ast.next_node_id()
    cloned_decl = ast.clone(params_decl, new_id)

    # for d in cloned_decl:
    #     # it's ok to rename here because it was cloned above
    #     d['name'] += '_' + d['id']

    # TODO: need to return the remapping and do it outside of this function
    # rename_map = { decl[i]['id']: cloned_decl[i]['id'] for i in range(len(decl)) }
    # def rename_ids(node, parent):
    #     # if node['nodeType'] == 'VariableDeclaration':
    #     #     node['name'] += '_2'

    #     if node['nodeType'] == 'Identifier':
    #         if node['referencedDeclaration'] in rename_map:
    #             node['name'] += '_2'
    #             node['referencedDeclaration'] = rename_map[node['referencedDeclaration']]

    # for d in cloned_decl:
    #     ast.walk_tree(d, callback=rename_ids)

    tuple_expr = make_tuple(arg_values)
    assignment_ids = [d['id'] for d in cloned_decl]
    var_dec = {
        "assignments": assignment_ids,
        "declarations": cloned_decl,
        "id": new_id,
        "initialValue": tuple_expr,
        "nodeType": "VariableDeclarationStatement"
    }

    return var_dec

# TODO: this does not embed parameters :(
def embed_modifiers_inplace(fd_node):
    # kind = baseConstructorSpecifier  is implied Super.Body + This.body
    # kind = modifierInvocation depends on the PlaceholderStatement
    def replace_placeholder(node, parent):
        if node['nodeType'] == 'PlaceholderStatement':
            # TODO: by now it's really clear I need a library to update parent_id and such hotswap/inject/attach/etc.
            clone_body = ast.clone(fd_node['body'], node['parent_id'])
            node.clear()
            node.update(clone_body)

    while fd_node.get('modifiers'):
        mod = fd_node['modifiers'].pop()
        mod_def = ast.by_id[mod['modifierName']['referencedDeclaration']]
        mod_body = ast.clone(mod_def['body'], fd_node['id'])
        ast.walk_tree(mod_body, callback=replace_placeholder)
        fd_node['body'] = mod_body

        mod_args = mod.get('arguments')
        if mod_args:
            vds = make_var_dec_st_from_func_call(mod_def['parameters']['parameters'], mod_args)
            fd_node['body']['statements'].insert(0, vds)

    return True


def embed_inline_func_inplace(fc_node):
    if 'referencedDeclaration' not in fc_node['expression']: # ['nodeType'] == 'MemeberAccess':
        return False # this is likely an external call (TODO: test Super.func and I guess public funcs)
    
    ref_id = fc_node['expression']['referencedDeclaration']
    func_dec = ast.by_id.get(ref_id)
    if not func_dec:
        return False

    if 'body' not in func_dec:
        return False # TODO: check when body is empty (calls on interfaces?)
    
    # TODO: walk the body to replace identifiers referncing the func_dec params
    # TODO: embed modifiers first?
    cloned_func = ast.clone(func_dec)
    embed_modifiers_inplace(cloned_func)

    inline_body = cloned_func['body']
    inline_body['parent_id'] = fc_node['parent_id']

    #embed_modifiers_inplace(inline_body) # TODO: need to replace func_dec not func_dec['body']
    # create VariableDeclarations (decl_params) = (passed_args)
    vds = make_var_dec_st_from_func_call(func_dec['parameters']['parameters'], fc_node['arguments'])
    vds['documentation'] = '@inlined from ' + func_dec['name']
    vds['parent_id'] = inline_body['id']
    inline_body['statements'].insert(0, vds)

    # for some reason documentation does not work on block bodies :(
    # if 'documentation' not in inline_body:
    #     inline_body['documentation'] = { 'id': ast.next_node_id(), 'nodeType': 'StructuredDocumentation', 'text': '', 'src': '0:0:0' }
    # inline_body['documentation']['text'] = ' @dev PATCHED!!!'

    fc_node.clear()
    fc_node.update(inline_body)
    return True

def embed_inline(_ast, contract_name, method_name, embed_modifiers=True, max_depth=-1):
    global ast
    ast = _ast

    target_func = None
    target_contract = None
    for func_node in ast.by_type['FunctionDefinition']:
        # TODO: it is possible to lookup FuncDef['scope'] to get the contract node id
        if func_node['name'] != method_name:
            continue

        tmp = ast.first_parent(func_node, 'ContractDefinition')
        if tmp and tmp['name'] == contract_name:
            target_func = func_node
            target_contract = tmp
            break

    if not target_func:
        return False
        
    # first, embed modifiers (TODO: need to embed modifiers for FunctionCall too)
    # TODO: fix reparenting here
    if embed_modifiers:
        embed_modifiers_inplace(target_func)

    # while there are FunctionCalls, inline them
    while max_depth != 0:
        # TODO: get all FunctionCalls, recursively replace them (wrap them in Block)
        func_calls = []
        def find_related_func_call(node, parent):
            if node['nodeType'] != 'FunctionCall':
                return
        
            if node['kind'] == 'typeConversion':
                return

            # if no parent, it's just a type conversion on global scope..
            func_def = ast.first_parent(node, 'FunctionDefinition')
            if func_def != target_func:
               return

            tmp = ast.first_parent(node, 'ContractDefinition')
            if tmp['id'] in target_contract['linearizedBaseContracts']:
                func_calls.append(node)

        ast.walk_tree(ast.root, callback=find_related_func_call)
        #print(func_calls)
        #last_call = func_calls[-1]
        #parent = ast.by_id[last_call['parent_id']]

        count = 0
        for fc in func_calls:
            if embed_inline_func_inplace(fc):
                count += 1

        if count == 0:
            break

        max_depth -= 1

    return True
