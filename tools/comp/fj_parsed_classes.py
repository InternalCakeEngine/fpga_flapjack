# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Classes that constitute the output of the parser and transformer
#

# Top level of a single function definition
class FunctionDef():
    def __init__(self, name, params, return_type, code ):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.code = code

# A single code block.
class CodeBlock():
    def __init__(self,lines):
        self.lines = lines
        self.offset = 0
        self.parent = None

    def find_var_by_name( self, name ):
        for line in self.lines:
            if isinstance(line,LocalVar) and line.name==name:
                return line
        if self.parent:
            if isinstance(self.parent,list):
                for param in self.parent:
                    if param.name==name:
                        return param
            else:
                return self.parent.find_var_by_name(name)
        return None

# A single code line.
class CodeLine():
    def __init__(elf):
        self.cb = None

    def set_cb( self, cb ):
        self.cb = cb


# Used for both formal parameters and local variables.
class LocalVar(CodeLine):
    def __init__(self,name,vtype):
        self.type = vtype
        self.name = name
        self.offset = None
        self.initial = None

# An assignment statement.
class Assignment(CodeLine):
    def __init__(self,name,exp):
        self.name = name
        self.exp = exp

# A return statement.
class Return(CodeLine):
    def __init__(self,exp):
        self.exp = exp

# A node in an expression tree.
class ExpNode():
    IDEN = "iden"
    LIT = "lit"
    def __init__(self,operator,operands):
        self.operator = operator
        self.operands = operands

# The operator type at a non-lead nonde in an expression tree.
class ExpOp():
    def __init__(self,op):
        self.op = op


