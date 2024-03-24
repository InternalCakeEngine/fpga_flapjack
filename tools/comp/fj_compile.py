# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Generate code.
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
    # Initialise register usage tracking.
    reg_usage = { "count": 0, "use": {} }
    for i in range(0,13):
        reg_usage["use"][i] = {"content": "free", "used":0}

    return _compile_block( fd.code, reg_usage )

def _compile_block( cb, reg_usage ):
    # Iterate over the codelines.
    res = []
    for codeline in cb.lines:
        codeline.compiled = None
        if isinstance(codeline,Assignment):
            assigned_var = cb.find_var_by_name( codeline.name )
            if assigned_var == None:
                print(f"Failed to find variable {codeline.name}")
                exit(1)
            dest_reg = get_free_reg(None,reg_usage)
            codeline.exp.dest_reg = dest_reg
            exp_code = compile_expression(cb,codeline.exp,reg_usage)
            reg_usage["use"][dest_reg] = {"content": assigned_var, "used":reg_usage["count"]}
            reg_usage["count"] += 1
            exp_code += [
                f"st r{dest_reg}, sp[{assigned_var.offset}]"
            ]
            codeline.compiled = exp_code
        elif isinstance(codeline,Return):
            codeline.exp.dest_reg = 0
            exp_code = compile_expression(cb,codeline.exp,reg_usage)
            codeline.compiled = exp_code+compile_return()
        if codeline.compiled:
            res += codeline.compiled
    return res
    

def compile_return():
    return ["ret"]

def compile_expression(cb,exp,reg_usage):
    output = []
    if exp.operator == ExpNode.IDEN:
        idenvar = cb.find_var_by_name( exp.operands[0] )
        if idenvar == None:
            print(f"Failed to find variable {exp.operands[0]}")
            exit(1)
        output.append(f"ld r{exp.dest_reg}, sp[{idenvar.offset}]")
    elif exp.operator == ExpNode.LIT:
        output.append(f"ld r{exp.dest_reg}, {exp.operands[0]}")
    else:
        for operand in exp.operands:
            operand.dest_reg = get_free_reg(None,reg_usage)
            operand.code = compile_expression(cb,operand,reg_usage)
        if exp.operator.op == "+":
            nodecode = [
                f"add r{exp.operands[0].dest_reg}, r{exp.operands[1].dest_reg}",
                f"mov r{exp.operands[1].dest_reg}, r{exp.dest_reg}"
            ]
        else:
            print(f"Encountered unknown operator {exp.operator}")
            exit(1)
        return exp.operands[0].code + exp.operands[1].code + nodecode
    return output

freer = 0
def get_free_reg( reqreg, reg_usage ):
    global freer
    if reqreg:
        return reqreg
    else:
        freer += 1
        return freer

        
    return output

