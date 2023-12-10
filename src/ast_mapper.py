import copy
from collections import defaultdict

class AstMapper:
    def __init__(self, root):
        self.root = root
        self.by_id = {}
        self.by_type = defaultdict(list)
        self.references_by_id = defaultdict(list)

        # create node mappings (eg. id -> node, type -> nodes[], etc.)
        self.walk_tree(self.root, callback=self._map_node)

        # TODO: move this here
        self.max_id = max(self.by_id.keys())

    def next_node_id(self):
        self.max_id += 1
        return self.max_id

    def _map_node(self, node, parent):
        if 'id' in node:
            self.by_id[node['id']] = node

        if parent and 'id' in parent:
            node['parent_id'] = parent['id']

        self.by_type[node['nodeType']].append(node)
        if 'referencedDeclaration' in node:
            self.references_by_id[node['referencedDeclaration']].append(node)

    # TODO: remove parent, can just set parent of all children in the map callback
    def walk_tree(self, node, parent=None, callback=None):
        # TODO: need to verify there isn't an identifier named "id", eg. some "exportedSymbol", etc.
        if type(node) is not dict or 'nodeType' not in node:
            return
        
        if callback:
            callback(node, parent)

        # TODO: perhaps it is better to only try to walk nodes[], body, parameters[], and some?
        for child in node.values():
            if type(child) is list:
                for grandchild in child:
                    self.walk_tree(grandchild, node, callback)
            else:
                self.walk_tree(child, node, callback)

    def clone(self, node, parent_id=None):
        # TODO: see if need to fix referenceDeclarations too
        remapping = {}
        def fix_ids(node, parent):
            new_id = self.next_node_id()
            # it seems Yul* nodes don't have ids (TODO: ensure all nodes have an id?)
            if 'id' in node:
                remapping[node['id']] = new_id
            node['id'] = new_id
            self.by_id[new_id] = node
            if parent:
                node['parent_id'] = parent['id']
            elif 'parent_id' not in node:
                del node['parent_id']

        def remap_assignments(node, parent):
            # TODO: use parent?
            if 'assignments' in node:
                node['assignments'] = [remapping.get(id, id) for id in node['assignments']]

        if type(node) is list:
            return [self.clone(child, parent_id) for child in node]

        # TODO: will need to re-map tree on every change... (can diff by references? or just re-map all?)
        node = copy.deepcopy(node)
        # TODO: more remappings, or perhaps move outside?
        self.walk_tree(node, callback=fix_ids)
        self.walk_tree(node, callback=remap_assignments)
        
        if parent_id:
            node['parent_id'] = parent_id

        return node

    def first_parent(self, node, *types):
        while 'parent_id' in node:
            node = self.by_id.get(node['parent_id'])
            if not node:
                return None # TODO: this is an error?

            if node['nodeType'] in types:
                return node

        return None
