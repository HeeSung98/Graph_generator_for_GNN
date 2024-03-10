from Graph_generator_for_GNN.parsing.cfg_class.CFG import CFG
from Graph_generator_for_GNN.parsing.cfg_class.Node import Node
from Graph_generator_for_GNN.parsing.cfg_class.GlobalCounter import GlobalCounter

node_counter = GlobalCounter()
function_counter = GlobalCounter()
variable_counter = GlobalCounter()
state_variable_counter = GlobalCounter()
function_dict = dict()
variable_dict = dict()
state_variable_dict = dict()


cfg_list = []

def test(node, cfg = None, pre_node = None, ifEnd_node = None):
    # If문 처리부
    node_id = node_counter.counter()
    condition_node = Node("Condition", node_id)
    pre_node.add_successor(condition_node.id)
    cfg.add_node(condition_node)
    traverse(node['condition'], cfg, condition_node)

    traverse(node['TrueBody'], cfg, condition_node)
    if cfg.last_node().name != "return":
        cfg.last_node().add_successor(ifEnd_node.id)

    if not node['FalseBody']:
        condition_node.add_successor(ifEnd_node.id)
    elif node['FalseBody']['type'] == 'IfStatement':
        test(node['FalseBody'], cfg, condition_node, ifEnd_node)
    else:
        traverse(node['FalseBody'], cfg, condition_node)
        if cfg.last_node().name != "return":
            cfg.last_node().add_successor(ifEnd_node.id)

# 노드를 받아와 해당 노드에서 feature를 문자열로 리턴
def create_feature(node):
    feature = ""

    if isinstance(node, list):
        for item in node:
            if isinstance(item, dict):
                feature += create_feature(item)
        return feature

    # 함수 표현
    elif node['type'] == 'FunctionCall':
        if node['expression']['type'] == 'Identifier':
            name = node['expression']['name']


            # # 함수명 딕셔너리에 해당 키가 없으면 생성
            # if name not in function_dict:
            #     function_dict[name] = str(function_counter.counter())

            if name in function_dict:
                #feature += "function" + function_dict[name] + ' ( ' ##########################################################
                feature += name + ' ( '
            else:
                feature += name + ' ( '


            length = len(node['arguments'])
            for i in range(length):
                if i == 0:
                    feature += create_feature(node['arguments'][i])
                else:
                    feature += ' , ' + create_feature(node['arguments'][i])
            feature += ' ) '
            return feature

        # variable.push() 이런애들
        elif node['expression']['type'] == 'MemberAccess':
            feature = create_feature(node['expression']) + ' ( '
            length = len(node['arguments'])
            for i in range(length):
                if i == 0:
                    feature += create_feature(node['arguments'][i])
                else:
                    feature += ' , ' + create_feature(node['arguments'][i])
            feature += ' ) '
            return feature

    # 점
    elif node['type'] == 'MemberAccess':
        if node['memberName'] in function_dict:
            feature = create_feature(node['expression']) + ' . ' + "function" + function_dict[node['memberName']]
        else:
            feature = create_feature(node['expression']) + ' . ' + node['memberName']
        return feature

    # for문에서 변수 선언부의 자료형 제거 + '=' 생성
    elif node['type'] == 'VariableDeclarationStatement':
        # ast구조에 예외가 없다는 가정하에 진행한 내용
        if node['initialValue'] == None:
            feature = create_feature(node['variables'])
        else:
            feature = create_feature(node['variables']) + " = " + create_feature(node['initialValue'])
        return feature
    elif node['type'] == 'ElementaryTypeName':
        return feature

    # 중위식 표현
    elif node['type'] == 'BinaryOperation':
        feature = create_feature(node['left']) + ' ' + node['operator'] + ' ' + create_feature(node['right'])
        return feature

    # 증감 연산자 표현
    elif node['type'] == 'UnaryOperation':
        #전위
        if node['isPrefix'] == True:
            feature = node['operator'] + ' ' + create_feature(node['subExpression'])
        #후위
        elif node['isPrefix'] == False:
            feature =  create_feature(node['subExpression']) + ' ' + node['operator']
        return feature

    # 배열
    elif node['type'] == 'IndexAccess':
        feature = create_feature(node['base']) + ' [ ' + create_feature(node['index']) + ' ] '
        return feature

    # 튜플 처리
    elif node['type'] == 'TupleExpression':
        length = len(node['components'])
        for i in range(length):
            if node['components'][i] == None:
                node['components'][i] = {'type': 'Identifier', 'name': 'None'}

            if i == 0:
                feature += " ( " + create_feature(node['components'][i])
            else:
                feature += " , " + create_feature(node['components'][i])
        feature += " ) "

        return feature


    for key, value in node.items():
        if isinstance(value, dict):
            feature += create_feature(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    feature += create_feature(item)

        elif isinstance(value, str):
            if key == 'name':
                if value == 'None':
                    feature += 'None'
                elif value in state_variable_dict:
                    #feature += "state_variable" + state_variable_dict[value] ##########################################################
                    feature += value
                elif value  in variable_dict:
                    #feature += "variable" + variable_dict[value] ##########################################################
                    feature += value
                else:
                    variable_dict[value] = str(variable_counter.counter())
                    #feature += "variable" + variable_dict[value] ##########################################################
                    feature += value
            elif key == 'number':
                if '.' in value:
                    #feature += 'decimal' ##########################################################
                    feature += value
                else:
                    #feature += 'integer' ##########################################################
                    feature += value
            elif key == 'operator':
                feature += value
            elif key == 'visibility':
                feature += value
            elif key == 'value':
                feature += 'string' ##########################################################
        elif isinstance(value, bool):
            if key == 'value':
                if value == True:
                    feature += 'True'
                elif value == False:
                    feature += 'False'

    return feature


def processing_assembly_line(node):
    node_type = node['type']
    assembly_feature = ""

    if node_type == 'AssemblyLocalDefinition':
        if node['names'][0]['name'] not in variable_dict:
            variable_dict[node['names'][0]['name']] = str(variable_counter.counter())
        # assembly_feature += node['names'][0]['name'] + ' = ' ################################ 변수는 여기서 선언하는 거라서 딕셔너리에 추가해서 사용한다
        assembly_feature += 'variable' + variable_dict[node['names'][0]['name']] + ' = '
        assembly_feature += processing_assembly_line(node['expression'])
    elif node_type == 'AssemblyExpression':
        if node['functionName'] in function_dict:
            assembly_feature += 'function' + function_dict[node['functionName']] + ' ( '
        else:
            assembly_feature += node['functionName'] + ' ( ' ################################ 함수는 기존에 있는 것 가져오는 경우 밖에 없으므로 추가 작업 x

        length = len(node['arguments'])
        for i in range(length):
            if i == 0:
                assembly_feature += processing_assembly_line(node['arguments'][i])
            else:
                assembly_feature += ' , ' + processing_assembly_line(node['arguments'][i])
        assembly_feature += ' ) '
    elif node_type == 'DecimalNumber' or node_type == 'HexNumber':
        assembly_feature += 'integer'
        # assembly_feature += node['value'] ################################
    elif node_type == 'AssemblyIf':
        assembly_feature += 'if ( ' + processing_assembly_line(node['condition'])
        assembly_feature += ' ) { ' + processing_assembly_line(node['body']['operations'][0])  + ' } '
    elif node_type == 'AssemblySwitch':
        assembly_feature += 'switch ' + 'variable' + variable_dict[node['expression']['functionName']] + ' { '################################
        for case in node['cases']:
            if 'value' in case:
                assembly_feature += ('case ' + case['value']['value'] + ' { ' +
                                     processing_assembly_line(case['block']['operations'][0])) + ' } '
            else:
                assembly_feature += 'default { ' + processing_assembly_line(case['block']['operations'][0]) + ' } '
        assembly_feature += ' } '

    return assembly_feature


def processing_assembly_block(node):

    assembly_feature = ""

    for children in node['body']['operations']:
        assembly_feature += '\n' + processing_assembly_line(children)

    return assembly_feature



def conditional_statement_processing(node, cfg=None):
    # Block 하위 리스트 순회
    for children in node['statements']:

        # return; 처리
        if children == None:
            return_node = Node("return", node_counter.counter())
            cfg.last_node().add_successor(return_node.id)
            cfg.add_node(return_node)
            return
        # break; 처리
        if children == ';':
            break_node = Node("break", node_counter.counter())
            cfg.last_node().add_successor(break_node.id)
            cfg.add_node(break_node)
            return


        node_type = children['type']
        last_node = cfg.last_node()

        # 어셈블리 처리
        if node_type == 'InLineAssemblyStatement':
            if last_node.name == 'Expression':
                cfg.last_node().feature.append(processing_assembly_block(children))
            else:
                node_id = node_counter.counter()
                expression_node = Node("Expression", node_id)

                (cfg.last_node()).add_successor(expression_node.id)
                cfg.add_node(expression_node)

                cfg.last_node().feature.append(processing_assembly_block(children))


        # 정의 처리부
        if node_type == 'ExpressionStatement':
            if last_node.name == 'Expression':
                traverse(children['expression'], cfg, cfg.last_node())
            else:
                node_id = node_counter.counter()
                expression_node = Node("Expression", node_id)

                (cfg.last_node()).add_successor(expression_node.id)
                cfg.add_node(expression_node)

                traverse(children['expression'], cfg, expression_node)

        # 선언 및 정의
        elif node_type == 'VariableDeclarationStatement':
            if children['initialValue']:
                if last_node.name == 'Expression':
                    traverse(children, cfg, cfg.last_node())
                else:
                    node_id = node_counter.counter()
                    expression_node = Node("Expression", node_id)

                    (cfg.last_node()).add_successor(expression_node.id)
                    cfg.add_node(expression_node)

                    traverse(children, cfg, expression_node)

        # 리턴 처리부
        elif (node_type == 'Identifier' or node_type == 'BinaryOperation'
              or node_type == 'NumberLiteral' or node_type == 'IndexAccess'
                or node_type == 'FunctionCall' or node_type == 'MemberAccess'
                or node_type == 'TupleExpression' or node_type == 'BooleanLiteral'):
            node_id = node_counter.counter()
            return_node = Node("return", node_id)
            return_node.feature.append("\n" + create_feature(children))
            cfg.last_node().add_successor(return_node.id)
            cfg.add_node(return_node)

        # throw; 처리
        elif node_type == 'ThrowStatement':
            node_id = node_counter.counter()
            throw_node = Node("throw", node_id)
            throw_node.feature.append("\n" + create_feature(children))
            cfg.last_node().add_successor(throw_node.id)
            cfg.add_node(throw_node)

        # If문 처리부
        elif node_type == 'IfStatement':
            ifendcount = 0
            node_id = node_counter.counter()
            condition_node = Node("Condition", node_id)
            (cfg.last_node()).add_successor(condition_node.id)
            cfg.add_node(condition_node)
            traverse(children['condition'], cfg, condition_node)

            node_id = node_counter.counter()
            ifEnd_node = Node("IfEnd", node_id)

            # True
            if children['TrueBody'] == None or children['TrueBody']['type'] != 'Block':
                test_dict = {}
                list = []
                test_dict['type'] = 'Block'
                list.append(children['TrueBody'])
                test_dict['statements'] = list
                traverse(test_dict, cfg, condition_node)
            else:
                traverse(children['TrueBody'], cfg, condition_node)

            if cfg.last_node().name != "return":
                cfg.last_node().add_successor(ifEnd_node.id)
            else:
                ifendcount += 1

            # False
            if not children['FalseBody']:
                condition_node.add_successor(ifEnd_node.id)
            elif children['FalseBody']['type'] == 'IfStatement':
                test(children['FalseBody'], cfg, condition_node, ifEnd_node)
            elif children['FalseBody']['type'] != 'Block':
                test_dict = {}
                list = []
                test_dict['type'] = 'Block'
                list.append(children['FalseBody'])
                test_dict['statements'] = list
                traverse(test_dict, cfg, condition_node)
            else:
                traverse(children['FalseBody'], cfg, condition_node)

                if cfg.last_node().name != "return":
                    cfg.last_node().add_successor(ifEnd_node.id)
                else:
                    ifendcount += 1

            if ifendcount == 2:
                pass
            else:
                cfg.add_node(ifEnd_node)

        # While문 처리부
        elif node_type == 'WhileStatement':
            node_id = node_counter.counter()
            loopCondition_node = Node("Condition", node_id)
            (cfg.last_node()).add_successor(loopCondition_node.id)
            cfg.add_node(loopCondition_node)
            traverse(children['condition'], cfg, loopCondition_node)

            if children['body']['type'] != 'Block':
                test_dict = {}
                list = []
                test_dict['type'] = 'Block'
                list.append(children['body'])
                test_dict['statements'] = list
                traverse(test_dict, cfg, loopCondition_node)
            else:
                traverse(children['body'], cfg, loopCondition_node)
            (cfg.last_node()).add_successor(loopCondition_node.id)

            node_id = node_counter.counter()
            whileEnd_node = Node("WhileEnd", node_id)
            cfg.add_node(whileEnd_node)
            loopCondition_node.add_successor(whileEnd_node.id)

        # For문 처리부
        elif node_type == 'ForStatement':

            if children['initExpression'] == None:
                pass
            else:
                node_id = node_counter.counter()
                VariableDeclaration_node = Node("LoopVariable", node_id)
                (cfg.last_node()).add_successor(VariableDeclaration_node.id)
                cfg.add_node(VariableDeclaration_node)
                traverse(children['initExpression'], cfg, VariableDeclaration_node)

            node_id = node_counter.counter()
            loopCondition_node = Node("Condition", node_id)
            (cfg.last_node()).add_successor(loopCondition_node.id)
            cfg.add_node(loopCondition_node)
            traverse(children['conditionExpression'], cfg, loopCondition_node)

            if children['body']['type'] != 'Block':
                test_dict = {}
                list = []
                test_dict['type'] = 'Block'
                list.append(children['body'])
                test_dict['statements'] = list
                traverse(test_dict, cfg, loopCondition_node)
            else:
                traverse(children['body'], cfg, loopCondition_node)

            node_id = node_counter.counter()
            loopExpression_node = Node("LoopExpression", node_id)
            cfg.last_node().add_successor(loopExpression_node.id)
            cfg.add_node(loopExpression_node)
            traverse(children['loopExpression']['expression'], cfg, loopExpression_node)
            (cfg.last_node()).add_successor(loopCondition_node.id)

            node_id = node_counter.counter()
            forEnd_node = Node("ForEnd", node_id)
            cfg.add_node(forEnd_node)
            loopCondition_node.add_successor(forEnd_node.id)



def create_cfg(node):

    cfg = CFG()
    node_id = node_counter.counter()
    function_node = Node("Function", node_id)
    cfg.add_node(function_node)
    traverse(node['body'], cfg, function_node)

    # FunctionEnd
    node_id = node_counter.counter()
    functionend_node = Node("FunctionEnd", node_id)
    for node in cfg.nodes:
        if not node.successors:
            node.add_successor(functionend_node.id)
    cfg.add_node(functionend_node)
    return cfg


def traverse(node, cfg=None, prev_node=None):
    node_type = node.get('type')

    if not node_type:
        return

    # 함수선언부
    elif node_type == 'FunctionDefinition':

        if node['name'] not in function_dict:
            function_dict[node['name']] = str(function_counter.counter())

        if isinstance(node['body'], list):
            pass
        elif not node['body']['statements']:
            pass
        else:
            cfg_list.append(create_cfg(node))
        return

    elif node_type == 'StateVariableDeclaration':
        for x in node['variables']:
            state_variable_dict[x['name']] = str(state_variable_counter.counter())
        return

    # 함수 외부에서 선언 및 선언 & 정의 / 이벤트 정의 등은 사용하지 않음
    elif (node_type == 'UsingForDeclaration' or node_type == 'EnumDefinition'
          or node_type == 'InheritanceSpecifier' or node_type == 'EventDefinition'
          or node_type == 'PragmaDirective' or node_type == 'ModifierDefinition' or node_type == 'StructDefinition'):
        return
    # 연산자 + 단순 식별자(condition 단일값) + 점 연산자 + 배열
    elif (node_type == 'BinaryOperation' or node_type == 'UnaryOperation'
          or node_type == 'Identifier' or node_type == 'MemberAccess' or node_type == 'IndexAccess'
          or node_type == 'TupleExpression' or node_type == 'BooleanLiteral' or node_type == 'NumberLiteral'):
        prev_node.feature.append("\n" + create_feature(node))

        return
    # for문 변수 선언부 or 변수에 값 할당
    elif node_type == 'VariableDeclarationStatement' or node_type == 'ExpressionStatement':
        prev_node.feature.append("\n" + create_feature(node))
        return
    # FunctionCall
    elif node_type == 'FunctionCall':
        prev_node.feature.append("\n" + create_feature(node))
        return

    if node_type == 'SourceUnit' or node_type == 'ContractDefinition':
        current_node = None
    else:
        node_id = node_counter.counter()
        current_node = Node(node_type, node_id)
        cfg.add_node(current_node)

    if prev_node:
        prev_node.add_successor(current_node.id)

    if node_type == 'Block':
        conditional_statement_processing(node, cfg)
        return

    for key, value in node.items():
        if isinstance(value, dict):
            traverse(value, cfg, current_node)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    traverse(item, cfg, current_node)


##################################################################################################################

def ast_to_cfg(ast):
    print(' ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ AstToCFG start ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ ')
    traverse(ast)

    viz_code = 'digraph G {\nnode[shape=box, style=rounded, fontname="Sans"]\n'

    for cfg in cfg_list:
        viz_code += cfg.cfg_to_dot()
    viz_code += '}'

    print(' ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ AstToCFG done ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ ')
    return viz_code
