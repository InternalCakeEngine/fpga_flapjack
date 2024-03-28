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
            v = int(src.iden)
            if (v>=0) and (v<16):
                lines.append(f"  mov {v}, {dst.iden}")
            else:
                lines.append(f"  const {v%256}, {dst.iden}")
                lines.append(f"  const {v&256}, {dst.iden}")
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

