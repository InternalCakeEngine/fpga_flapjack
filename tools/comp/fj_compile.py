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
from fj_usertypes import find_var_offset

def fj_compile( proot ):
    label_state = { "next": 0 }
    ir_res = []
    for entity in proot:
        if isinstance(entity,FunctionDef):
            entity.code.stackextent = entity.stackextent
            compiled_code = _compile_func( entity, label_state )
            ir_res.append( {
                "name":entity.name,
                "ir":compiled_code,
                "stackextent": entity.stackextent
            })
            #for line in compiled_code:
            #    try:
            #        print(line.pretty())
            #    except:
            #        pass
        elif isinstance(entity,AsmLine):
            ir_res.append( {
                "name": "__litasm",
                "litstr": entity.str
            })
    return ir_res


def _compile_func( fd, label_state ):
    ssa_state = { "next":0 }
    return _compile_block( fd.code, ssa_state, label_state, True )

def _compile_block( cb, ssa_state, label_state, is_top_level ):
    # Iterate over the codelines.
    res = []
    if not is_top_level:
        if cb.stackextent>0:
            res += [ IrStep("stack_extend", [IrLoc("c",cb.stackextent)], None ) ]
    for codeline in cb.lines:
        codeline.compiled = None
        if isinstance(codeline,Assignment):
            if codeline.name == "_":
                assigned_var = None
            else:
                assigned_var = cb.find_var_by_name( codeline.name )
                if assigned_var == None:
                    print(f"Failed to find variable {codeline.name}")
                    exit(1)
            dest_sa = get_next_sa(ssa_state)
            codeline.exp.dest_sa = dest_sa
            exp_code = compile_expression(cb,codeline.exp,ssa_state,label_state)
            if assigned_var:
                varoffset = find_var_offset( assigned_var, codeline.name )
                exp_code += [ IrStep("store",[IrLoc("sa",dest_sa)],IrLoc("l",varoffset)) ]
            codeline.compiled = exp_code
        elif isinstance(codeline,Return):
            if codeline.exp == None:
                codeline.compiled=[]
                codeline.compiled = compile_return(None,cb.stackextent,True)
            else:
                codeline.exp.dest_sa = get_next_sa(ssa_state)
                exp_code = compile_expression(cb,codeline.exp,ssa_state,label_state)
                codeline.compiled = exp_code+compile_return(codeline.exp.dest_sa,cb.stackextent,False)
        elif isinstance(codeline,WhileLoop):
            codeline.exp.dest_sa = get_next_sa(ssa_state)
            exp_code = compile_expression(cb,codeline.exp,ssa_state,label_state)
            codeline.code_block.stackextent = cb.stackextent
            body_code = _compile_block(codeline.code_block,ssa_state,label_state,False)
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
        elif isinstance(codeline,IfElse):
            codeline.exp.dest_sa = get_next_sa(ssa_state)
            exp_code = compile_expression(cb,codeline.exp,ssa_state,label_state)
            codeline.code_block.stackextent = cb.stackextent
            body_code_if   = _compile_block( codeline.code_block_if,   ssa_state, label_state, False )
            body_code_else = None
            if codeline.code_block_else:
                codeline.code_block.stackextent = cb.stackextent
                body_code_else = _compile_block( codeline.code_block_else, ssa_state, label_state, False )
            else_label = get_next_label(label_state)
            end_label = get_next_label(label_state)
            codeline.compiled  = exp_code
            codeline.compiled += [
                IrStep("cmp", [IrLoc("c",0),IrLoc("sa",codeline.exp.dest_sa)], None),
                IrStep("branch_cond", [else_label,IrLoc("cc","eq")], None)
            ]
            codeline.compiled += body_code_if
            if body_code_else:
                codeline.compiled += [
                    IrStep("branch_cond", [end_label,IrLoc("cc","a")], None),
                    IrStep("label",[else_label],None)
                ]
                codeline.compiled += body_code_else
            else:
                codeline.compiled += [ IrStep("label",[else_label],None) ]
            codeline.compiled += [ IrStep("label",[end_label],None) ]
        if codeline.compiled:
            res += codeline.compiled
    if not is_top_level:
        if cb.stackextent>0:
            res += [ IrStep("stack_retract", [IrLoc("c",cb.stackextent)], None ) ]
    return res
    

def compile_return(sa,spdelta,isempty):
    if isempty:
        return [ IrStep("ret",[None,IrLoc("c",spdelta)],None) ]
    else:
        return [ IrStep("ret",[IrLoc("sa",sa),IrLoc("c",spdelta)],None) ]

def compile_expression(cb,exp,ssa_state,label_state):
    output = []
    if exp.operator == ExpNode.IDEN:
        idenvar = cb.find_var_by_name( exp.operands[0] )
        if idenvar == None:
            print(f"Failed to find variable {exp.operands[0]}")
            exit(1)
        varoffset = find_var_offset( idenvar, exp.operands[0] )
        output.append( IrStep("load", [IrLoc("l",varoffset)], IrLoc("sa",exp.dest_sa)) )
    elif exp.operator == ExpNode.LIT:
        output.append( IrStep("const", [IrLoc("lab",exp.operands[0])],IrLoc("sa",exp.dest_sa)) )
    elif exp.operator == ExpNode.CALL:
        plist = [ IrLoc("a",exp.operands[0]) ]
        for param in exp.operands[1:]:
            param.dest_sa = get_next_sa(ssa_state)
            output += compile_expression(cb,param,ssa_state,label_state)
            plist += [ IrLoc("sa",param.dest_sa) ]
        output += [ IrStep("call", plist, IrLoc("sa",exp.dest_sa)) ]
    else:
        for operand in exp.operands:
            operand.dest_sa = get_next_sa(ssa_state)
            operand.code = compile_expression(cb,operand,ssa_state,label_state)
        if exp.operator.op == "+":
            nodecode = [ IrStep("add", [IrLoc("sa",exp.operands[0].dest_sa),IrLoc("sa",exp.operands[1].dest_sa)], IrLoc("sa",exp.dest_sa) ) ]
        elif exp.operator.op in ["<<",">>","&","|"]:
            oname = {"<<":"shl",">>":"shr","&":"and","|":"or"}[exp.operator.op]
            nodecode = [ IrStep(oname, [IrLoc("sa",exp.operands[1].dest_sa),IrLoc("sa",exp.operands[0].dest_sa)], IrLoc("sa",exp.dest_sa) ) ]
        elif exp.operator.op in ["<",">"]:
            hop_label = get_next_label(label_state)
            if exp.operator.op == ">":
                compflags = "gt"    # Result is greater-than
            else:
                compflags = "lt"    # Result is less-than
            nodecode = [
                IrStep("load", [IrLoc("c",1)], IrLoc("sa",exp.dest_sa)),
                IrStep("cmp", [IrLoc("sa",exp.operands[0].dest_sa),IrLoc("sa",exp.operands[1].dest_sa)], None ),
                IrStep("branch_cond", [hop_label,IrLoc("cc",compflags)],None),
                IrStep("load", [IrLoc("c",0)], IrLoc("sa",exp.dest_sa)),
                IrStep("label",[hop_label],None)
            ]
        elif exp.operator.op=="!=" or exp.operator.op=="==":
            hop_label = get_next_label(label_state)
            if exp.operator.op == "!=":
                v1 = 1
                v2 = 0
            else:
                v1 = 0
                v2 = 1
            nodecode = [
                IrStep("load", [IrLoc("c",v1)], IrLoc("sa",exp.dest_sa)),
                IrStep("cmp", [IrLoc("sa",exp.operands[0].dest_sa),IrLoc("sa",exp.operands[1].dest_sa)], None ),
                IrStep("branch_cond", [hop_label,IrLoc("cc","eq")],None),
                IrStep("load", [IrLoc("c",v2)], IrLoc("sa",exp.dest_sa)),
                IrStep("label",[hop_label],None)
            ]
        else:
            print(f"Encountered unknown operator {exp.operator.op}")
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

