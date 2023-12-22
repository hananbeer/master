from collections import defaultdict

# https://solidity-ast.netlify.app/interfaces/contractdefinition

class SolidityAstRebuilder:
    def __init__(self, ast):
        self.ast = ast
        self.context = defaultdict(list)

    def build(self):
        self.code = ''
        self.depth = 0
        self.visit_node(self.ast)
        return self.code
    
    def write(self, text):
        self.code += text

    def newline(self):
        self.write('\n')

    def writeline(self, text):
        self.write(text + '\n')

    def tab(self):
        if self.code[-1] == '\n':
            text = '    ' * self.depth
            self.write(text)

    def push(self, text):
        self.writeline(text)
        self.depth += 1

    def pop(self):
        self.depth -= 1
        # annoying hack to avoid empty lines when closing brackets
        while self.code[-2:] == '\n\n':
            self.code = self.code[:-1]
        self.tab()
        self.write('}\n\n')

    def visit_node(self, node):
        node_type = node.get('nodeType')
        handler = getattr(self, 'process_' + node_type, self.process_unknown)
        res = handler(node)
        node['visited'] = True
        return res

    def process_SourceUnit(self, node):
        # TODO: rebuild node['license']
        for child in node.get('nodes', []):
            self.visit_node(child)

    def process_PragmaDirective(self, node):
        items = node['literals']
        language = items[0]
        self.writeline(f'pragma {language} {"".join(items[1:])};\n')

    def process_StructuredDocumentation(self, node):
        raise Exception('TODO: StructuredDocumentation')

    def process_UsingForDirective(self, node):
        # TODO: ..
        self.tab()
        self.write('using ')
        self.visit_node(node['libraryName'])
        self.write(' for ')
        if 'typeName' in node:
          self.visit_node(node['typeName'])
        else:
          self.write('*')
        #self.writeline(';\n')

    def process_IdentifierPath(self, node):
        self.write(node['name'])

    def process_ElementaryTypeName(self, node):
        self.write(node['name'])
        if 'stateMutability' in node and node['stateMutability'] != 'nonpayable' :
            self.write(' ' + node['stateMutability'])

    def process_ElementaryTypeNameExpression(self, node):
        if node['typeName'].get('stateMutability') == 'payable':
            self.write('payable')
        else:
            self.visit_node(node['typeName'])

    def process_UserDefinedTypeName(self, node):
        self.visit_node(node['pathNode'])

    def process_ContractDefinition(self, node):
        if node.get('abstract'):
            self.write('abstract ')
        
        self.write(node['contractKind'] + ' ')
        self.write(node['name'])
        
        # inheritence
        if node['baseContracts']:
            self.write(' is ')
            for i, base in enumerate(node['baseContracts']):
                if i > 0:
                    self.write(', ')

                self.visit_node(base)

        self.push(' {')

        for child in node.get('nodes', []):
            self.visit_node(child)
            if 'body' not in child:
                self.writeline(';')
        
        self.pop()
    
    def process_EnumDefinition(self, node):
        self.push('enum ' + node['name'] + ' {')
        for child in node.get('members', []):
            self.visit_node(child)
            if 'body' not in child:
                self.writeline(';')
        
        self.pop()
    
    def process_StructDefinition(self, node):
        self.push('struct ' + node['name'] + ' {')
        for child in node.get('members', []):
            self.visit_node(child)
            if 'body' not in child:
                self.writeline(';')
        
        self.pop()
    
    def process_EnumValue(self, node):
        self.writeline(node['name'] + ',')
    
    def process_InheritanceSpecifier(self, node):
        self.visit_node(node['baseName'])

        # TODO: test this
        if 'arguments' in node:
            self.visit_list(node['arguments'], True)

    def process_TupleExpression(self, node):
        self.visit_list(node['components'], True)

    def process_UncheckedBlock(self, node):
        self.tab()
        self.push('unchecked {')
        # seems to be the same logic
        self.process_Block(node)
        self.pop()

    def process_FunctionCallOptions(self, node):
        self.visit_node(node['expression'])
        if 'options' in node:
            self.write('{ ')
            for i in range(len(node['options'])):
                if i > 0:
                    self.write(', ')

                name = node['names'][i]
                self.write(f"{name}: ")
                self.visit_node(node['options'][i])

            self.write(' }')

    def process_FunctionDefinition(self, node):
        #self.write('\n')
        self.tab()
        if node['kind'] == 'constructor':
            self.write('constructor')
        elif node['kind'] == 'fallback':
            self.write('fallback')
        elif node['kind'] == 'receive':
            self.write('receive')
        elif node['kind'] == 'function':
            self.write(f"function {node['name']}")
        else: #elif node['kind'] == 'freeFunction':
            raise Exception('unsupported function kind!')

        self.visit_node(node['parameters'])
        
        # only show visibility for functions (& free functions?)
        if node['kind'] != 'constructor':
            self.write(f" {node['visibility']}")

        if node['stateMutability'] != 'nonpayable':
            self.write(' ' + node['stateMutability'])

        if node['virtual']:
            self.write(' virtual')

        for modifier in node.get('modifiers', []):
            self.write(' ')
            self.visit_node(modifier)

        # TODO: override
        if 'returnParameters' in node and node['returnParameters']['parameters']:
            self.write(' returns ')
            self.visit_node(node['returnParameters'])

        if node['implemented']:
            self.push(' {')
            self.visit_node(node['body'])
            self.pop()
        else:
            pass # self.write(';')

    def process_ModifierDefinition(self, node):
        #self.write('\n')
        self.tab()
        self.write('modifier ' + node['name'])
        self.visit_node(node['parameters'])
        self.push(' {')
        self.visit_node(node['body'])
        self.pop()

    def process_ModifierInvocation(self, node):
        self.write(node['modifierName']['name'])
        if 'arguments' in node:
            self.visit_list(node['arguments'], True)

    def process_PlaceholderStatement(self, node):
        self.tab()
        self.writeline('_;')

    def process_ParameterList(self, node):
        self.write('(')
        for i, param in enumerate(node['parameters']):
            if i > 0:
                self.write(', ')

            self.visit_node(param)

        self.write(')')

    def process_Block(self, node):
        # TODO: semicolon and newlines should probably be put here instead of everywhere else
        for statement in node.get('statements', []):
            #self.tab()
            self.visit_node(statement)

    def process_Literal(self, node):
        # TODO: ..
        if node['kind'] == 'string':
            self.write(f'"{node["value"]}"')
        else:
            self.write(node['value'])

    def process_Identifier(self, node):
        self.tab()
        self.write(node['name'])

    def process_Assignment(self, node):
        self.tab()
        self.visit_node(node['leftHandSide'])
        self.write(' ' + node['operator'] + ' ')
        self.visit_node(node['rightHandSide'])

    def process_MemberAccess(self, node):
        self.visit_node(node['expression'])
        self.write('.')
        self.write(node['memberName'])

    def process_IndexAccess(self, node):
        self.visit_node(node['baseExpression'])
        self.write('[')
        self.visit_node(node['indexExpression'])
        self.write(']')

    def process_UnaryOperation(self, node):
        if node['prefix']:
            self.write(node['operator'])
            self.visit_node(node['subExpression'])
        else:
            self.visit_node(node['subExpression'])
            self.write(node['operator'])

    def process_BinaryOperation(self, node):
        self.visit_node(node['leftExpression'])
        self.write(' ' + node['operator'] + ' ')
        self.visit_node(node['rightExpression'])

    def process_VariableDeclaration(self, node):
        self.tab()
        self.visit_node(node['typeName'])

        if node['storageLocation'] != 'default':
            self.write(' ' + node['storageLocation'])

        # NOTE: contract level variables will have 'internal' omitted but is ok imo
        if node['visibility'] != 'internal':
            self.write(' ' + node['visibility'])

        if node['constant']:
            self.write(' constant')

        if node.get('indexed'):
            self.write(' indexed')

        if 'name' in node and node['name']:
            self.write(' ' + node['name'])

        if 'value' in node:
            self.write(' = ')
            self.visit_node(node['value'])

    def process_VariableDeclarationStatement(self, node):
        self.tab()
        self.visit_list(node['declarations'])
        if 'initialValue' in node:
            self.write(' = ')
            self.visit_node(node['initialValue'])

        self.writeline(';')

    def process_Mapping(self, node):
        self.write('mapping(')
        self.visit_node(node['keyType'])
        self.write(' => ')
        self.visit_node(node['valueType'])
        self.write(')')

    def process_ArrayTypeName(self, node):
        self.visit_node(node['baseType'])
        self.write('[')
        if 'length' in node:
            self.visit_node(node['length'])
        self.write(']')

    def process_EventDefinition(self, node):
        self.tab()
        self.write('event ' + node['name'])
        self.visit_node(node['parameters'])
        #self.writeline(');')

    def process_ErrorDefinition(self, node):
        self.tab()
        self.write('error ' + node['name'])
        self.visit_node(node['parameters'])
        #self.writeline(');')

    def visit_list(self, args, brackets=False):
        # TODO: figure out context to wrap or not
        if brackets or len(args) > 1:
            self.write('(')

        for i, arg in enumerate(args):
            if i > 0:
                self.write(', ')

            if arg:
                self.visit_node(arg)

        if brackets or len(args) > 1:
            self.write(')')

    def process_EmitStatement(self, node):
        self.tab()
        self.write('emit ')
        self.visit_node(node['eventCall'])
        self.writeline(';')

    def process_ExpressionStatement(self, node):
        self.visit_node(node['expression'])
        self.writeline(';')

    def process_FunctionCall(self, node):
        self.visit_node(node['expression'])
        self.visit_list(node['arguments'], True)

    def process_IfStatement(self, node):
        self.tab()
        self.write('if (')
        self.visit_node(node['condition'])
        self.push(') {')
        self.visit_node(node['trueBody'])
        if 'falseBody' in node:
            self.depth -= 1
            self.tab()
            self.write('} else {\n')
            self.depth += 1
            self.visit_node(node['falseBody'])
        
        self.pop()

    def process_Conditional(self, node):
        #self.tab()
        self.write('(')
        self.visit_node(node['condition'])
        self.write(' ? ')
        self.visit_node(node['trueExpression'])
        self.write(' : ')
        self.visit_node(node['falseExpression'])
        self.write(')')

    def process_NewExpression(self, node):
        #self.tab()
        self.write('new ???') # TODO: ..
        # self.visit_node(node['expression'])

    def process_FunctionTypeName(self, node):
        #self.tab()
        self.write('**FunctionTypeName**??') # TODO: ..
        # self.visit_node(node['expression'])

    def process_ForStatement(self, node):
        # print(', '.join(node.keys()))
        self.tab()
        self.write('for (')
        if 'initializationExpression' in node:
          self.visit_node(node['initializationExpression'])
          self.code = self.code[:-2] # hack to remove the newline + semicolon
        self.write('; ')
        self.visit_node(node['condition'])
        self.write('; ')
        if 'loopExpression' in node:
          self.visit_node(node['loopExpression'])
          self.code = self.code[:-2] # hack to remove the newline + semicolon
        self.push(') {')
        self.visit_node(node['body'])
        self.pop()

    def process_WhileStatement(self, node):
        self.tab()
        self.write('while (')
        self.visit_node(node['condition'])
        self.push(') {')
        self.visit_node(node['body'])
        self.pop()

    def process_Break(self, node):
        self.tab()
        self.write('break')

    def process_RevertStatement(self, node):
        self.tab()
        self.write('revert(')
        if 'expression' in node:
            self.visit_node(node['expression'])
        self.writeline(');')

    def process_Return(self, node):
        self.tab()
        self.write('return')
        if 'expression' in node:
            self.write(' ')
            self.visit_node(node['expression'])
        self.writeline(';')

    def process_UserDefinedValueTypeDefinition(self, node):
        self.tab()
        self.write('type ??') # TODO: ..

    def process_InlineAssembly(self, node):
        self.tab()
        self.push('assembly {')
        self.visit_node(node['AST'])
        self.pop()

    def process_YulBlock(self, node):
        self.tab()
        # TODO: is this the same?
        self.process_Block(node)
        
    def process_YulAssignment(self, node):
        self.tab()
        self.visit_list(node['variableNames'])
        self.write(' := ')
        self.visit_node(node['value'])
        self.write('\n')

    def process_YulIdentifier(self, node):
        self.tab()
        self.write(node['name'])
        
    def process_YulFunctionCall(self, node):
        self.tab()
        self.visit_node(node['functionName'])
        self.visit_list(node['arguments'], True)
        
    def process_YulVariableDeclaration(self, node):
        self.tab()
        self.write('let ')
        self.visit_list(node['variables'])
        self.write(' := ')
        self.visit_node(node['value'])
        
    def process_YulTypedName(self, node):
        self.tab()
        self.write(node['name'])
        
    def process_YulLiteral(self, node):
        self.tab()
        self.write(node['value'])
        
    def process_YulExpressionStatement(self, node):
        self.tab()
        self.visit_node(node['expression'])

    def process_unknown(self, node):
        print(f"\n**{node['nodeType']}**\n")
        exit(0)
        # raise Exception('unknown or missing node type!')
