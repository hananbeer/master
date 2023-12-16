import os
import sys
import json
import argparse
import fileinput
import importlib

import mutators
from ast_mapper import AstMapper

def ast_from_config(build_config):
    build_json = json.loads(build_config)
    tree = build_json.get('ast')
    if not tree:
        sources = build_json['sources']
        tree = sources[list(sources.keys())[0]]['AST']

    return AstMapper(tree)


def list_mutators():
    mutators = []
    for filename in os.listdir('./src/mutators'):
        if filename.endswith('.py') and not filename.startswith('__'):
            mutators.append(filename[:-3])

    return mutators


parser = argparse.ArgumentParser('main', add_help=False)
parser.add_argument('input_file', nargs='?', help='input build json file; use "-" for stdin')
parser.add_argument('mutator',  nargs='?', help='mutator name')
parser.add_argument('--list', action='store_true', help='list mutators')
args, remaining_args = parser.parse_known_args()

if args.list:
    for mutator in list_mutators():
        print(mutator)

    exit(1)

if not args.mutator:
    parser.print_help()
    exit(1)

build_config = ''.join(fileinput.input(args.input_file))
ast = ast_from_config(build_config)
mutator_name = os.path.basename(args.mutator)
module = importlib.import_module(f'mutators.{mutator_name}')
res = module.run_cli(ast, remaining_args)
if res:
    # TODO: should res be the ast/tree or just bool?
    data = { "sources": { "MASTER.sol": { "AST": ast.root } } }
    print(json.dumps(data))
    exit(0)
else:
    exit(1)

