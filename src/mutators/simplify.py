required_keys = [
    'id',
    'parent_id',
    'nodeType',
    'nodes',
    'body',
    'name',
    'statements',
    'assignments',
    'arguments',
    'expression',
    'initializationExpression',
    'indexExpression',
    'leftExpression',
    'rightExpression',
    'loopExpression',
    'subExpression',
    'baseExpression',
    'baseContracts',
    'referencedDeclaration',
    'memberName',
    'implemented',
    'kind',
    'modifiers',
    'parameters',
    'returnParameters',
    'constant',
    'mutability',
    'visibility',
    'anonymous',
    'documentation',
    'scope',
    'stateMutability',
    'storageLocation',
    'typeName',
    'virtual',
    'initialValue',
    'value',
    'leftHandSide',
    'rightHandSide',
    'trueBody',
    'falseBody',
    'operator',
    'eventCall',
    'functionName',
    'absolutePath',
    'license',
    'literals',
    'abstract',
    'canonicalName',
    'contractDependencies',
    'contractKind',
    'fullyImplemented',
    'linearizedBaseContracts',
    'AST',
    'length',
    'libraryName',
    'modifierName',
    'indexed',

    # good to have
    'functionSelector',
    'eventSelector',
    'text',
    'tryCall',
    'isInlineArray',
    'evmVersion',

    # satisfy tools
    'src',
    'names',
    'nameLocations',
    'typeDescriptions',

    # seems to be needed or expected by tools
    'type',
    'variableNames',
    'variables',
    'valueName',
    'valueNameLocation',
    'valueType',
    'baseName',
    'stateVariable',
    'keyType',
    'options',
    'pathNode',
    'prefix',

    'components',
    'condition',
    'declarations',

    'baseType',
    'exportedSymbols',
        
    # uncertain if needed, stay on safe side
    'baseContract',
]

# TODO: remove
removed = set()
seen = set()

def simplify(ast):
    def remove_unnecessary_nodes(node, parent):
        for key in list(node.keys()):
            seen.add(key)
            if key not in required_keys:
                del node[key]
                removed.add(key)

    ast.walk_tree(ast.root, callback=remove_unnecessary_nodes)

    # debug:
    # import sys
    # keep = set()
    # for key in sorted(required_keys):
    #     if key not in seen:
    #         keep.add(key)
            
    # if len(keep) > 0:
    #     print('%s is not seen, better keep it' % keep, file=sys.stderr)
    # print(sorted(removed), file=sys.stderr)
    return True

def run_cli(ast, raw_args):
    return simplify(ast)
