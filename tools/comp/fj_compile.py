# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Generate IR with single assingment registers (to be resolved later).
#

# IR is in the form of tuples:
#  (op,[srcs],dsts)
# ...where srcs and dsts are tuples of (<type>,<value>) where
# type is "sa" for a single assignment location, "l" for a local,
# "c" for a const.
# 

from fj_parsed_classes import *
from fj_ir_classes import *

def fj_compile( proot ):
    label_state = { "next": 0 }
    ir_res = []
    for entity in proot:
        if isinstance(entity,FunctionDef):
            compiled_code = _compile_func( entity, label_state )
            ir_res.append( {
                "name":entity.name,
                "ir":compiled_code,
                "first_local": entity.param_local_limit,
                "next_local": entity.next_local
            })
    return ir_res


def _compile_func( fd, label_state ):
    ssa_state = { "next":0 }
    return _compile_block( fd.code, ssa_state, label_state )

def _compile_block( cb, ssa_state, label_state ):
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
            exp_code = compile_expression(cb,codeline.exp,ssa_state,label_state)
            exp_code += [ IrStep("store",[IrLoc("sa",dest_sa)],IrLoc("l",assigned_var.offset)) ]
            codeline.compiled = exp_code
        elif isinstance(codeline,Return):
            codeline.exp.dest_sa = get_next_sa(ssa_state)
            exp_code = compile_expression(cb,codeline.exp,ssa_state,label_state)
            codeline.compiled = exp_code+compile_return(codeline.exp.dest_sa)
        elif isinstance(codeline,WhileLoop):
            codeline.exp.dest_sa = get_next_sa(ssa_state)
            exp_code = compile_expression(cb,codeline.exp,ssa_state,label_state)
            body_code = _compile_block(codeline.code_block,ssa_state,label_state)
            top_label = get_next_label(label_state)
            end_label = get_next_label(label_state)
            codeline.compiled =  [
                # Stack extension goes in here.
                IrStep("label",[top_label],None)
            ]
            codeline.compiled += exp_code
            codeline.compiled += [
                IrStep("cmp", [IrLoc("c",0),IrLoc("sa",codeline.exp.dest_sa)], None),
                IrStep("branch_cond", [end_label,IrLoc("cc","eq")], None)
            ]
            codeline.compiled += body_code
            codeline.compiled += [
                IrStep("branch_cond", [top_label,IrLoc("cc","a")], None),
                IrStep("label",[end_label],None)
                # Stack retraction goes in here.
            ]
        if codeline.compiled:
            res += codeline.compiled
    return res
    

def compile_return(sa):
    return [ IrStep("ret",[IrLoc("sa",sa)],IrLoc('nop',None)) ]

def compile_expression(cb,exp,ssa_state,label_state):
    output = []
    if exp.operator == ExpNode.IDEN:
        idenvar = cb.find_var_by_name( exp.operands[0] )
        if idenvar == None:
            print(f"Failed to find variable {exp.operands[0]}")
            exit(1)
        output.append( IrStep("load", [IrLoc("l",idenvar.offset)], IrLoc("sa",exp.dest_sa)) )
    elif exp.operator == ExpNode.LIT:
        output.append( IrStep("const", [IrLoc("c",exp.operands[0])],IrLoc("sa",exp.dest_sa)) )
    else:
        for operand in exp.operands:
            operand.dest_sa = get_next_sa(ssa_state)
            operand.code = compile_expression(cb,operand,ssa_state,label_state)
        if exp.operator.op == "+":
            nodecode = [ IrStep("add", [IrLoc("sa",exp.operands[0].dest_sa),IrLoc("sa",exp.operands[1].dest_sa)], IrLoc("sa",exp.dest_sa) ) ]
        elif exp.operator.op == ">":
            hop_label = get_next_label(label_state)
            nodecode = [
                IrStep("load", [IrLoc("c",1)], IrLoc("sa",exp.dest_sa)),
                IrStep("cmp", [IrLoc("sa",exp.operands[0].dest_sa),IrLoc("sa",exp.operands[1].dest_sa)], None ),
                IrStep("branch_cond", [hop_label,IrLoc("cc","gt")],None),
                IrStep("load", [IrLoc("c",0)], IrLoc("sa",exp.dest_sa)),
                IrStep("label",[hop_label],None)
            ]
        else:
            print(f"Encountered unknown operator {exp.operator}")
            exit(1)
        return exp.operands[0].code + exp.operands[1].code + nodecode
    return output

def get_next_sa( ssa_state ):
    res = ssa_state["next"]
    ssa_state["next"]+=1
    return res

def get_next_label( label_state ):
    num = label_state["next"]
    label_state["next"]+=1
    return IrLoc("label",f"loc_{num}")

