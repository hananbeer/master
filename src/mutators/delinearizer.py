
# TODO: need to merge constructors and such
def delinearize(ast, contract_name):
    node = None
    for id_node in ast.by_type['ContractDefinition']:
        if id_node['name'] == contract_name:
            node = id_node
            break

    if not node:
        return False
    
    # inline inherited contract bodies (as is for now)
    base_ids = reversed(node['linearizedBaseContracts'][1:])
    for base_id in base_ids:
        base = ast.by_id[base_id]
        base_nodes = ast.clone(base['nodes'], node['id'])

        # TODO: comments are reordered with nodes using `solc-ast-compile`
        # and are not supported by builder yet
        # if len(base_nodes) > 0:
        #     doc = base_nodes[0].get('documentation', {'id': ast.next_node_id(), 'text': '', "nodeType": "StructuredDocumentation"})
        #     doc['text'] = f'\n@inherited from {base["name"]}\n' + doc['text']
        #     base_nodes[0]['documentation'] = doc

        node['nodes'] = base_nodes + node['nodes']

    # remove inherited contracts
    node['linearizedBaseContracts'] = node['linearizedBaseContracts'][:1]
    node['baseContracts'] = []
    return True

