import argparse

# TODO: flag to remove classes inherited from
# TODO: need to merge constructors and such (for now it can be done with the function inliner)
def delinearize(ast, contract_name):
    node = None
    for id_node in ast.by_type['ContractDefinition']:
        if id_node['name'] == contract_name:
            node = id_node
            break

    if not node:
        raise Exception('no contract found: "%s"' % contract_name)
        # return False

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

def run_cli(ast, raw_args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--contract', required=True, help='filter by contract name')
    args = parser.parse_args(raw_args)
    return delinearize(ast, args.contract)
