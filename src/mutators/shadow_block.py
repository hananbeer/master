def remove_blocks(ast):
    def lighten_up(node, parent):
        doc = node.get('documentation', '')
        if type(doc) is dict:
            doc = doc.get('text', '')

        if doc.strip() == 'shadow':
            parent['statements'].remove(node)

    ast.walk_tree(ast.root, callback=lighten_up)
