import sys
import json
from rebuilder import SolidityAstRebuilder

def print_ast(node, depth=0):
    print(f"""{'  ' * depth} {node.get('id', '-')} {node.get('nodeType', '/')} "{node.get('name', 'N/A')}" """)
    for child in node.get('nodes', []):
        print_ast(child, depth+1)

def main():
    args = sys.argv
    if len(args) != 2:
        print(f'Usage: {args[0]} <build_path>')
        exit(1)

    build_path = args[1]
    f = open(build_path, 'rb')
    build_config = json.load(f)
    f.close()

    if 'ast' in build_config:
        ast = build_config['ast']
    else:
        sources = list(build_config['sources'].items())
        if len(sources) != 1:
            # TODO: support multiple files
            raise Exception('expecting exactly one source file')

        source_path, source_data = sources[0]
        ast = source_data['AST']

    processor = SolidityAstRebuilder(ast)
    processor.build()
    print(processor.code)
    #print_ast(rebuilder.ast)

if __name__ == '__main__':
    main()
