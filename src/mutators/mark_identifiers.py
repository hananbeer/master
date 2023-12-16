
# rename all identifiers to include the respective id
def rename_all(ast):
    def rename_var_decs(node, parent):
        if node['nodeType'] == 'VariableDeclaration':
            node['name'] += '_' + str(node['id'])

    def rename_ids(node, parent):
        if node['nodeType'] == 'Identifier':
            # TODO: YulIdentifier doesn't seem to have referencedDeclaration so will have to search up the scope to
            # (probably best preprocess this to add [guessed] referencedDeclaration to YulIdentifier)
            ref_node = ast.by_id.get(node['referencedDeclaration'])
            if ref_node:
                node['name'] = ref_node['name']

    ast.walk_tree(ast.root, callback=rename_var_decs)
    ast.walk_tree(ast.root, callback=rename_ids)
    return True

def run_cli(_ast, raw_args):
    return rename_all(_ast)
