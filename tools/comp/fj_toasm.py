# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Take IR in reg-alloced form and output assembly code.
#

def fj_toasm( func_list ):
    for func in func_list:
        func["asm"] = _toasm_func( func["name"], func["ir"] )
        for instr in func["asm"]:
            print(instr)
    
    return []

def _toasm_func( funcname, funcir ):

    lines = [
        f"{funcname}:"
    ]
    
    for step in funcir:
        stepir = step["ir"]
        if stepir.op == "load":
            src = stepir.srcs[0]
            dst = stepir.dst
            if src.itype=="l" and dst.itype=="r":
                lines.append(f"  ld  sp[{src.iden}], {dst.iden}")
            elif src.itype=="c" and dst.itype=="r":
                lines.append(f"  mov  {src.iden}, {dst.iden}")
            else:
                lines.append(f"  BAD LOAD: {stepir.pretty()}")
        elif stepir.op == "store":
            src = stepir.srcs[0]
            dst = stepir.dst
            if src.itype=="r" and dst.itype=="l":
                lines.append(f"  st  {src.iden}, sp[{dst.iden}]")
            else:
                lines.append(f"  BAD STORE: {stepir.pretty()}")
        elif stepir.op == "call":
            param_count = len(stepir.srcs[1:])
            slist = list(step["inuse"])
            for save in slist:
                lines.append(f"  push {save}, sp")
            for param in stepir.srcs[1:]:
                lines.append(f"  push {param.iden}, sp")
            lines.append(f"  const hi({stepir.srcs[0].iden}), r0")
            lines.append(f"  const lo({stepir.srcs[0].iden}), r0")
            lines.append(f"  call r0")
            if param_count > 0:
                lines.append(f"  add {param_count}, sp")
            slist.reverse()
            for save in slist:
                lines.append(f"  pop sp, {save}")
            lines.append(f"  mov r0, {stepir.dst.iden}")
        elif stepir.op == "add":
            src = stepir.srcs[0]
            dst = stepir.dst
            if src.itype=="r" and src.itype=="r":
                lines.append(f"  add  {src.iden}, {dst.iden}")
            else:
                lines.append(f"  BAD ADD: {stepir.pretty()}")
        elif stepir.op == "ret":
            src = stepir.srcs[0]
            if src.itype=="r":
                lines.append(f"  mov  {src.iden}, r0")
                lines.append(f"  ret")
            else:
                lines.append(f"  BAD RET: {stepir.pretty()}")
        elif stepir.op == "const":
            src = stepir.srcs[0]
            dst = stepir.dst
            if src.itype=="c":
                v = int(src.iden)
                if (v>=0) and (v<16):
                    lines.append(f"  mov {v}, {dst.iden}")
                else:
                    lines.append(f"  const hi({v}), {dst.iden}")
                    lines.append(f"  const lo({v}), {dst.iden}")
            elif src.itype=="lab":
                lines.append(f"  const hi({src.iden}), {dst.iden}")
                lines.append(f"  const lo({src.iden}), {dst.iden}")
            else:
                lines.append(f"  BAD CONSTANT: {stepir.pretty()}")
        elif stepir.op == "label":
            lines.append(f"{stepir.srcs[0].iden}:")
        elif stepir.op == "cmp":
            src1 = stepir.srcs[0]
            src2 = stepir.srcs[1]
            if src1.itype=="c" and src2.itype=="r":
                lines.append(f"  cmp {src1.iden}, {src2.iden}")
            elif src1.itype=="r" and src2.itype=="r":
                lines.append(f"  cmp {src1.iden}, {src2.iden}")
            else:
                lines.append(f"  BAD COMPARE: {stepir.pretty()}")
        elif stepir.op == "branch_cond":
            src = stepir.srcs[0]
            cond = stepir.srcs[1].iden
            cc = {"a": "a", "eq":"e","neq":"E","gt":"g","ngt":"G"}.get(cond,"BAD")
            if src.itype=="label":
                lines.append(f"  br.{cc} {src.iden}")
            else:
                lines.append("  BAD BRANCH: {stepir.pretty()}")
        else:
            lines.append(f"Unknown IR op: {stepir.op}")

    return( lines )

