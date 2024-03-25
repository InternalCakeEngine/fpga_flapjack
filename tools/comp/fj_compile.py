# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Generate IR with single assingment registers (to be resolved later).
#

# IR is in the form of tuples:
#  (op,[srcs],[dsts])
# ...where srcs and dsts are tuples of (<type>,<value>) where
# type is "sa" for a single assignment location, "l" for a local,
# "c" for a const.
# 

from fj_parsed_classes import *

def fj_compile( proot ):
    for entity in proot:
        if isinstance(entity,FunctionDef):
            compiled_code = _compile_func( entity )
            entity.compiled = compiled_code
            for cl in compiled_code:
                print(cl)

def _compile_func( fd ):
    ssa_state = { "next":0 }
    return _compile_block( fd.code, ssa_state )

def _compile_block( cb, ssa_state ):
    # Iterate over the codelines.
    res = []
    for codeline in cb.lines:
        codeline.compiled = None
        if isinstance(codeline,Assignment):
            assigned_var = cb.find_var_by_name( codeline.name )
            if assigned_var == None:
                print(f"Failed to find variable {codeline.name}")
                exit(1)
            dest_sa = get_next_sa(ssa_state)
            codeline.exp.dest_sa = dest_sa
            exp_code = compile_expression(cb,codeline.exp,ssa_state)
            exp_code += [ ("store",[("sa",dest_sa)],[("l",assigned_var.offset)]) ]
            codeline.compiled = exp_code
        elif isinstance(codeline,Return):
            codeline.exp.dest_sa = get_next_sa(ssa_state)
            exp_code = compile_expression(cb,codeline.exp,ssa_state)
            codeline.compiled = exp_code+compile_return(codeline.exp.dest_sa)
        if codeline.compiled:
            res += codeline.compiled
    return res
    

def compile_return(sa):
    return [ ("ret",[("sa",sa)],[]) ]

def compile_expression(cb,exp,ssa_state):
    output = []
    if exp.operator == ExpNode.IDEN:
        idenvar = cb.find_var_by_name( exp.operands[0] )
        if idenvar == None:
            print(f"Failed to find variable {exp.operands[0]}")
            exit(1)
        output.append( ("load", [("l",idenvar.offset)], [("sa",exp.dest_sa)]) )
    elif exp.operator == ExpNode.LIT:
        output.append( ("const", [("c",exp.operands[0])],[("sa",exp.dest_sa)]) )
    else:
        for operand in exp.operands:
            operand.dest_sa = get_next_sa(ssa_state)
            operand.code = compile_expression(cb,operand,ssa_state)
        if exp.operator.op == "+":
            nodecode = [ ( ("add"), [("sa",exp.operands[0].dest_sa),("sa",exp.operands[1].dest_sa)], [("sa",exp.dest_sa)] ) ]
        else:
            print(f"Encountered unknown operator {exp.operator}")
            exit(1)
        return exp.operands[0].code + exp.operands[1].code + nodecode
    return output

def get_next_sa( ssa_state ):
    res = ssa_state["next"]
    ssa_state["next"]+=1
    return res
