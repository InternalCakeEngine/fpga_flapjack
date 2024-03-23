from lark import Lark, Transformer, v_args;

flapjack_grammar = '''

%import common.WS
%ignore WS

start: entity_list                                                                          -> childobj

entity_list: function_def                                                                   -> childobj_list
           | ( function_def entity_list )                                                   -> choldobjpair_list

function_def: "function" IDENTIFIER "(" formal_param_list ")" "->" type_name code_block     -> function_def

formal_param_list: formal_param_single                                                      -> childobj_list
                 | ( formal_param_single "," formal_param_list )                            -> childobjpair_list
formal_param_single: IDENTIFIER "->" type_name                                              -> var_declaration

type_name: "int16"

code_block: "{" code_line_list "}"                                                          -> ordered_code_block

code_line_list: code_line                                                                   -> childobj_list
              | ( code_line code_line_list )                                                -> childobjpair_list

code_line: code_block | ( ( var_decl_line | assignment_line | return_line ) ";" )           -> childobj

var_decl_line: "var" IDENTIFIER "->" type_name                                              -> var_declaration

assignment_line: "let" IDENTIFIER "=" expression                                            -> assignment

return_line: "return" expression                                                            -> func_return

expression: (   "(" expression ")" )                                                        -> exp_paren
          | binary_op_form                                                                  -> childobj
          | unary_prefix_op_form                                                            -> childobj
          | IDENTIFIER                                                                      -> exp_identifier
          | INT                                                                             -> exp_literal

binary_op_form: expression binary_op expression                                             -> exp_binary
unary_prefix_op_form: unary_prefix_op expression                                            -> exp_unary

binary_op: "+"                                                                              -> exp_binary_add
         | "-"                                                                              -> exp_binary_sub
         | "*"                                                                              -> exp_binary_mult
         | "/"                                                                              -> exp_binary_div
         | "&"                                                                              -> exp_binary_and
         | "|"                                                                              -> exp_binary_or
         | "=="                                                                             -> exp_binary_equal
         | "!="                                                                             -> exp_binary_nequal
         | ">"                                                                              -> exp_binary_gt
         | "<"                                                                              -> exp_binary_lt
unary_prefix_op: "-"                                                                        -> op_unary_negate

IDENTIFIER: CNAME

%import common.CNAME
%import common.INT
'''

class LocalVar():
    def __init__(self,vtype,name):
        self._type = vtype
        self._name = name
        self._offset = None
        self._initial = None

class CodeBlock():
    def __init__(self,parent,base_offset):
        self._parent = parent
        self._base_offset = base_offset
        self._locals = []

class ExpNode():
    IDEN = "iden"
    LIT = "lit"
    def __init__(self,operator,operands):
        _operator = operator
        _operands = operands

class FunctionDef():
    def __init__(self):
        pass

class Assignment():
    def __init__(self,name,exp):
        _name = name
        _exp = exp

class Return():
    def __init__(self,exp):
        _exp = exp

class ExpOp():
    def __init__(self,op):
        _op = op

class Function():
    def __init__(self, name, params, return_type, code ):
        _name = name
        _params = params
        _return_type = return_type
        _code = code

@v_args(inline=True)
class CollectElements(Transformer):

    def __init__(self):
        self.functions = {}

    def childobj( self, o ):
        return o

    def childobj_list( self, o ):
        return [o]

    def childobjpair_list( self, o1, o2 ):
        return [o1]+o2

    def function_def(self, func_name, param_list, return_type, code_block ):
        return Function( func_name, param_list, return_type, code_block )

    def ordered_code_block(self,cb):
        return cb

    def codelines(self,c):
        return c

    def assignment( self, name, exp ):
        return Assignment( name, exp )

    def formal_param( self, vtype, name ):
        return LocalVar( name, vtype )

    def var_declaration( self, name, vtype ):
        return LocalVar( name, vtype )

    def func_return( self, exp ):
        return Return( exp )

    def exp_paren( self, expression ):
        return self.exp_param( expression )

    def exp_binary( self, o1, op, o2 ):
        return ExpNode( op, [o1,o2] )

    def exp_unary( self, op, o1 ):
        return ExpNode( op, [o1] )

    def exp_identifier( self, i ):
        return ExpNode( ExpNode.IDEN, [i] )

    def exp_literal( self, l ):
        return ExpNode( ExpNode.LIT, [l] )

    def exp_binary_add(self):
        return ExpOp("+")
    def exp_binary_sub(self):
        return ExpOp("-")
    def exp_binary_mult(self):
        return ExpOp("*")
    def exp_binary_div(self):
        return ExpOp("/")
    def exp_binary_and(self):
        return ExpOp("&")
    def exp_binary_or(self):
        return ExpOp("|")
    def exp_binary_equal(self):
        return ExpOp("==")
    def exp_binary_nequal(self):
        return ExpOp("!=")
    def exp_binary_gt(self):
        return ExpOp(">")
    def exp_binary_lt(self):
        return ExpOp("<")
    def exp_unary_negate(self):
        return ExpOp("-")

fjl_parser = Lark( flapjack_grammar, parser="lalr", transformer=CollectElements() )
fjl = fjl_parser.parse

def main():
    with open("test.oats","r") as infile:
        inlines = "\n".join(infile.readlines())
    print( fjl(inlines) )


if __name__ == '__main__':
    main()





