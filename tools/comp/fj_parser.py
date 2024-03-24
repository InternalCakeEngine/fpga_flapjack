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

entity_list: function_def                                                                   -> childobj_list
           | ( function_def entity_list )                                                   -> choldobjpair_list

function_def: "function" IDENTIFIER "(" formal_param_list ")" "->" type_name code_block     -> function_def

formal_param_list: formal_param_single                                                      -> childobj_list
                 | ( formal_param_single "," formal_param_list )                            -> childobjpair_list
formal_param_single: IDENTIFIER "->" type_name                                              -> var_declaration

type_name: builtin_typename                                                                 -> childobj

builtin_typename: "int16"                                                                   -> stringlit_int16

code_block: "{" code_line_list "}"                                                          -> ordered_code_block

code_line_list: code_line                                                                   -> childobj_list
              | ( code_line code_line_list )                                                -> childobjpair_list

code_line: code_block                                                                       -> childobj
         | ( ( var_decl_line | assignment_line | return_line ) ";" )                        -> childobj

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


@v_args(inline=True)
class CollectElements(Transformer):

    def __init__(self):
        self.functions = {}

    def stringlit_int16(self):
        return( "int16" )

    def childobj( self, o ):
        return o

    def childobj_list( self, o ):
        return [o]

    def childobjpair_list( self, o1, o2 ):
        return [o1]+o2

    def function_def(self, func_name, param_list, return_type, code_block ):
        return FunctionDef( func_name, param_list, return_type, code_block )

    def ordered_code_block(self,linelist):
        return CodeBlock(linelist)

    def assignment( self, name, exp ):
        return Assignment( name, exp )

    def formal_param( self, vtype, name ):
        return LocalVar( name, vtype )

    def var_declaration( self, name, vtype ):
        return LocalVar( name, vtype )

    def typename_int16( self ):
        return("int16")

    def func_return( self, exp ):
        return Return( exp )

    def exp_paren( self, expression ):
        return expression

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

_fj_generated = Lark( _flapjack_grammar, parser="lalr", transformer=CollectElements() )
fj_parser = _fj_generated.parse

