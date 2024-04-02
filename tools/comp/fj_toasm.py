# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Take IR in reg-alloced form and output assembly code.
#

def fj_toasm( entity_list ):
    for entity in entity_list:
        if entity["name"] == "__litasm":
            print(entity["litstr"][1:-1])
        else:
            entity["asm"] = _toasm_func( entity["name"], entity["ir"], entity["stackextent"] )
            for instr in entity["asm"]:
                print(instr)
    
    return []

def _toasm_func( funcname, funcir, initial_stack_extent ):

    lines = [
        f"{funcname}:",
        f"  sub {initial_stack_extent+1}, sp",
        f"  st  ct, sp[{initial_stack_extent}]" # Only necessary for non-leaf functions.
    ]

    stack_offset = initial_stack_extent
    for step in funcir:
        stepir = step["ir"]
        if stepir.op=="stack_extend":
            src = stepir.srcs[0]
            lines.append(f"  sub {src.iden}, sp")
            stack_offset += src.iden
        elif stepir.op=="stack_retract":
            src = stepir.srcs[0]
            lines.append(f"  add {src.iden}, sp")
            stack_offset -= src.iden
        elif stepir.op == "load":
            src = stepir.srcs[0]
            dst = stepir.dst
            if src.itype=="l" and dst.itype=="r":
                lines.append(f"  ld  sp[{stack_offset+src.iden}], {dst.iden}   # stack_offset={stack_offset}, src.iden={src.iden}")
            elif src.itype=="c" and dst.itype=="r":
                lines.append(f"  mov  {src.iden}, {dst.iden}")
            else:
                lines.append(f"  BAD LOAD: {stepir.pretty()}")
        elif stepir.op == "store":
            src = stepir.srcs[0]
            dst = stepir.dst
            if src.itype=="r" and dst.itype=="l":
                lines.append(f"  st  {src.iden}, sp[{stack_offset+dst.iden}]")
            else:
                lines.append(f"  BAD STORE: {stepir.pretty()}")
        elif stepir.op == "call":
            param_count = len(stepir.srcs[1:])
            savelist = [ save for save in  list(step["inuse"]) if save not in [p.iden for p in stepir.srcs[1:]] ]
            pushlist = savelist + [param.iden for param in stepir.srcs[1:] ]
            lines.append(f"  sub {len(pushlist)}, sp");
            for i,push in enumerate(pushlist):
                lines.append(f"  st {push}, sp[{len(pushlist)-(i+1)}]")
            lines.append(f"  const hi({stepir.srcs[0].iden}), r0")
            lines.append(f"  const lo({stepir.srcs[0].iden}), r0")
            lines.append(f"  call r0")
            savelist.reverse()
            for i,save in enumerate(savelist):
                lines.append(f"  ld {save}, sp[{len(pushlist)-(i+1)}]")
            lines.append(f"  add {len(pushlist)}, sp");
            if stepir.dst.iden:
                lines.append(f"  mov r0, {stepir.dst.iden}")
        elif stepir.op == "add":
            src1 = stepir.srcs[0]
            src2 = stepir.srcs[1]
            dst = stepir.dst
            if src2.itype=="r" and dst.itype=="r" and src2.iden != dst.iden:
                lines.append(f"  BAD 3OP")
            else:
                if src1.itype=="r" and dst.itype=="r":
                    lines.append(f"  add  {src1.iden}, {dst.iden}")
                else:
                    lines.append(f"  BAD ADD: {stepir.pretty()}")
        elif stepir.op in ["shl","shr","and","or"]:
            src1 = stepir.srcs[0]
            src2 = stepir.srcs[1]
            dst = stepir.dst
            if src2.itype=="r" and dst.itype=="r" and src2.iden != dst.iden:
                lines.append(f"  BAD 3OP")
            oname = {"shl":"shl","shr":"shr","and":"and","or":"or"}[stepir.op]
            if src1.itype=="r" and dst.itype=="r":
                lines.append(f"  {oname}  {src1.iden}, {dst.iden}")
            elif src1.itype=="c" and dst.itype=="r":
                lines.append(f"  {oname}  {src1.iden}, {dst.iden}")
            else:
                lines.append(f"  BAD OP: {stepir.pretty()}")
        elif stepir.op == "ret":    # Only from top level of function atm. Needs stack_offset handling.
            if stack_offset != initial_stack_extent:
                lines.append("  BAD RET: mid func exit")
            else:
                src = stepir.srcs[0]
                if src:
                    if src.itype=="r":
                        lines.append(f"  mov  {src.iden}, r0")
                    else:
                        lines.append(f"  BAD RET: {stepir.pretty()}")
                lines.append(f"  ld sp[{initial_stack_extent}], ct")
                lines.append(f"  ret {stepir.srcs[1].iden+1}")
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
            cc = {"a": "a", "eq":"e","neq":"E","gt":"g","lt":"GE","ngt":"G"}.get(cond,f"BAD (from {cond})")
            if src.itype=="label":
                lines.append(f"  br.{cc} {src.iden}")
            else:
                lines.append("  BAD BRANCH: {stepir.pretty()}")
        else:
            lines.append(f"Unknown IR op: {stepir.op}")

    return( lines )

