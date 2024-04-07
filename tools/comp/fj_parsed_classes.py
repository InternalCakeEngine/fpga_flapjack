# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Classes that constitute the output of the parser and transformer
#

# Top level (only) line of assembly
class AsmLine():
    def __init__(self, literal ):
        self.str = literal

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

    def find_var_by_name( self, iden ):
        for line in self.lines:
            if isinstance(line,LocalVar) and line.name==iden.names[0]:
                return line
        if self.parent:
            if isinstance(self.parent,list):
                for param in self.parent:
                    if param.name==iden.names[0]:
                        return param
            else:
                return self.parent.find_var_by_name(iden)
        else:
            # We should look in the global namespace here but we have no route to it (yet).
            pass
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

# A while loop.
class WhileLoop(CodeLine):
    def __init__(self,exp,code_block):
        self.exp = exp
        self.code_block = code_block 

# A while loop.
class IfElse(CodeLine):
    def __init__(self,exp,code_block_if,code_block_else):
        self.exp = exp
        self.code_block_if = code_block_if
        self.code_block_else = code_block_else

# A return statement.
class Return(CodeLine):
    def __init__(self,exp):
        self.exp = exp

# A node in an expression tree.
class ExpNode():
    IDEN = "iden"
    LIT = "lit"
    CALL = "call"
    EMPTY = "empty"
    def __init__(self,operator,operands):
        self.operator = operator
        self.operands = operands
        self.utype = None

# The operator type at a non-lead nonde in an expression tree.
class ExpOp():
    def __init__(self,op):
        self.op = op

class ExpSubscript():
    def __init__(self,exp,sublist):
        self.exp = exp
        self.sublist = sublist

class ExpRef():
    def __init__(self,exp):
        self.exp = exp


# Definition of a struct
class StructDef():
    def __init__(self,name,elemlist):
        self.name = name
        self.elemlist = elemlist

    def __str__(self):
        return f"struct {self.name} {{ [e for e in self.elemlist] }}"

class StructElemDef():
    def __init__(self,name,elemtype):
        self.name = name
        self.elemtype = elemtype

    def __str__(self):
        return f"{self.name}->{self.elemtype})"

# Type shenannigans as parsed (processed version in fj_type_classes.py.
class SimpleTypeUse():
    def __init__(self,typename):
        self.typename = typename

    def __str__(self):
        return f"{self.typename}"

    def __eq__(self,other):
        return isinstance(other,SimpleTypeUse) and self.typename == other.typename

class RefTypeUse():
    def __init__(self,wrapped):
        self.wrapped = wrapped

    def __str__(self):
        return f"ref({self.wrapped})"

    def __eq__(self,other):
        return isinstance(other,RefTypeUse) and self.wrapped == other.wrapped


class UserTypeUse():
    def __init__(self,typename):
        self.typename = typename

    def __str__(self):
        return f"ref({self.typename})"

    def __eq__(self,other):
        return isinstance(other,UserTypeUse) and self.typename == other.typename

class Identifier():
    def __init__(self,names,subs):
        self.names = names
        self.subs = subs        # Only for assginement targets. Probably.

    def __str__(self):
        return ".".join(self.names)
