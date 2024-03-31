# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Grammar and transformer provided to the Lark library.
#

from lark import Lark, Transformer, v_args;

from fj_parsed_classes import *

_flapjack_grammar = '''

%import common.WS
%ignore WS

start: entity_list                                                                          -> childobj

entity_list: top_level_entity                                                               -> childobj_list
           | ( top_level_entity entity_list )                                               -> childobjpair_list

top_level_entity: function_def                                                              -> childobj
                | asm_line                                                                  -> childobj

asm_line: "_asm" "(" string  ")" ";"                                                        -> asm_literal_line

function_def: "function" IDENTIFIER "(" formal_params_or_not ")" "->" type_name code_block  -> function_def

formal_params_or_not: "empty"                                                               -> empty_list
                    | formal_params                                                         -> childobj
formal_params: formal_param_single                                                          -> childobj_list
                 | ( formal_param_single "," formal_params )                                -> childobjpair_list
formal_param_single: IDENTIFIER "->" type_name                                              -> var_declaration

type_name: builtin_typename                                                                 -> childobj

builtin_typename: "int16"                                                                   -> stringlit_int16
                | "empty"                                                                   -> stringlit_empty

code_block: "{" code_line_list "}"                                                          -> ordered_code_block

code_line_list: code_line                                                                   -> childobj_list
              | ( code_line code_line_list )                                                -> childobjpair_list

code_line: code_block                                                                       -> childobj
         | ( ( var_decl_line | assignment_line | while_line | if_line | return_line ) )     -> childobj

var_decl_line: "var" IDENTIFIER "->" type_name ";"                                          -> var_declaration

assignment_line: "let" IDENTIFIER "=" expression ";"                                        -> assignment

while_line: "while" "(" expression ")" code_block                                           -> while_loop
if_line: ( "if"    "(" expression ")" code_block "else" code_block )                        -> ifelse
       | ( "if"    "(" expression ")" code_block  )                                         -> ifonly

return_line: "return" expression ";"                                                        -> func_return
           | "return" "empty" ";"                                                           -> func_return_empty

expression: (   "(" expression ")" )                                                        -> exp_paren
          | binary_op_form                                                                  -> childobj
          | unary_prefix_op_form                                                            -> childobj
          | function_call                                                                   -> childobj
          | IDENTIFIER                                                                      -> exp_identifier
          | INT                                                                             -> exp_literal

function_call: IDENTIFIER "(" call_params_or_not ")"                                        -> exp_call

call_params_or_not: "empty"                                                                 -> empty_list
                  | call_params                                                             -> childobj
call_params: call_param_single                                                              -> childobj_list
                 | ( call_param_single "," call_params )                                    -> childobjpair_list
call_param_single: expression                                                               -> childobj

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
         | ">>"                                                                             -> exp_binary_sright
         | "<<"                                                                             -> exp_binary_sleft
unary_prefix_op: "-"                                                                        -> op_unary_negate

string: ESCAPED_STRING                                                                      -> childobj
IDENTIFIER: CNAME

%import common.ESCAPED_STRING
%import common.CNAME
%import common.INT
'''


@v_args(inline=True)
class CollectElements(Transformer):

    def __init__(self):
        self.functions = {}

    def stringlit_int16(self):
        return( "int16" )

    def stringlit_empty(self):
        return( "empty" )

    def tokenstring(self,token):
        return(token.value)

    def childobj( self, o ):
        return o

    def empty_list( self ):
        return []

    def childobj_list( self, o ):
        return [o]

    def childobjpair_list( self, o1, o2 ):
        return [o1]+o2

    def function_def(self, func_name, param_list, return_type, code_block ):
        return FunctionDef( func_name, param_list, return_type, code_block )

    def asm_literal_line(self, string_token):
        return AsmLine( string_token.value )

    def ordered_code_block(self,linelist):
        return CodeBlock(linelist)

    def assignment( self, name, exp ):
        return Assignment( name, exp )

    def while_loop( self, exp, code_block ):
        return WhileLoop( exp, code_block )

    def ifelse( self, exp, code_block_if, code_block_else ):
        return IfElse( exp, code_block_if, code_block_else )

    def ifonly( self, exp, code_block_if ):
        return IfElse( exp, code_block_if, None )

    def formal_param( self, vtype, name ):
        return LocalVar( name, vtype )

    def var_declaration( self, name, vtype ):
        return LocalVar( name, vtype )

    def typename_int16( self ):
        return("int16")

    def func_return( self, exp ):
        return Return( exp )

    def func_return_empty( self ):
        return Return( None )

    def exp_paren( self, expression ):
        return expression

    def exp_call( self, name, params ):
        return ExpNode( ExpNode.CALL, [name]+params )

    def exp_binary( self, o1, op, o2 ):
        return ExpNode( op, [o1,o2] )

    def exp_unary( self, op, o1 ):
        return ExpNode( op, [o1] )

    def exp_identifier( self, i ):
        return ExpNode( ExpNode.IDEN, [i.value] )

    def exp_literal( self, l ):
        return ExpNode( ExpNode.LIT, [l.value] )

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
    def exp_binary_sright(self):
        return ExpOp(">>")
    def exp_binary_sleft(self):
        return ExpOp("<<")
    def exp_unary_negate(self):
        return ExpOp("-")

try:
    _fj_generated = Lark( _flapjack_grammar, parser="lalr", transformer=CollectElements() )
    fj_parser = _fj_generated.parse
except Exception as e:
    print("Exception building parser.")
    print(e)
    


