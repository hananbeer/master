import sys
import json

from ast_mapper import AstMapper

def ast_from_config(build_path):
    f = open(build_path, 'rb')
    build_config = json.load(f)
    f.close()

    tree = build_config.get('ast')
    if not tree:
        sources = build_config['sources']
        tree = sources[list(sources.keys())[0]]['AST']

    return AstMapper(tree)

build_path = './data/build.json'
ast = ast_from_config(build_path)

from mutators import mark_identifiers
DEBUG = True
if DEBUG:
    # note: this actually seems to fix var shadowing issues, for now;
    # but it's not the correct solution for the long term as the tree is out of sync
    mark_identifiers.rename_all(ast)

# from mutators import using_for_inliner
# using_for_inliner.embed_using_for(ast)

# from mutators import storage_relocator
# storage_relocator.patch_storage_slots(ast)

# from mutators import delinearizer
# delinearizer.delinearize(ast, 'Zapper_Matic_Bridge_V1_1')

from mutators import function_inliner
function_inliner.embed_inline(ast, 'Zapper_Matic_Bridge_V1_1', 'ZapBridge', embed_modifiers=True, max_depth=6)

# wrap AST in structure that satisfies solc
data = { "sources": { build_path: { "AST": ast.root } } }
print(json.dumps(data)) #, indent=4))
