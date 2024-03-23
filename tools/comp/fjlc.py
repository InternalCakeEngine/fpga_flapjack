from lark import Lark, Transformer, v_args;

flapjack_grammar = '''

%import common.WS
%ignore WS

start: entity_list

entity_list: function_def | ( function_def entity_list )

function_def: "function" IDENTIFIER "(" formal_param_list ")" "->" type_name code_block  -> function_def

formal_param_list: formal_param_single | ( formal_param_single "," formal_param_list )
formal_param_single: type_name IDENTIFIER

type_name: "int16"

code_block: "{" code_line_list "}"

code_line_list: code_line | ( code_line code_line_list )

code_line: code_block | ( ( var_decl_line | assignment_line | return_line ) ";" )

var_decl_line: "var" IDENTIFIER "->" type_name

assignment_line: "let" IDENTIFIER "=" expression 

return_line: "return" expression

expression: ( "(" expression ")" ) | binary_op_form | unary_prefix_op_form | IDENTIFIER

binary_op_form: expression binary_op expression
unary_prefix_op_form: unary_prefix_op expression

binary_op: "+" | "-" | "*" | "/" | "&" | "|" | "==" | "!=" | ">" | "<"
unary_prefix_op: "-"

IDENTIFIER: CNAME

%import common.CNAME
'''

@v_args(inline=True)
class CollectElements(Transformer):

    def __init__(self):
        self.functions = {}
        self.globals = {}
        self.imports = {}

    def function_def(self, func_name, param_list, return_type, code_block ):
        return(f"Definitions of {func_name}")



fjl_parser = Lark( flapjack_grammar, parser="lalr", transformer=CollectElements() )
fjl = fjl_parser.parse

def main():
    with open("test.oats","r") as infile:
        inlines = "\n".join(infile.readlines())
    print( fjl(inlines) )


if __name__ == '__main__':
    main()





