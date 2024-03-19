# WiP assembler for Flapjacks.
# (c) 2024 Martin Young.

# Currently outputs fully linked binaries for address 0.

import sys

def work():
    filenames = []
    for arg in sys.argv[1:]:
        if arg[0]=='-':
            print(f"Unknown flag {arg}. Exiting.")
            exit(1)
        else:
            filenames.append( arg )

    for filename in filenames:
        if filename[-2:] != ".s":
            print(f"Skipping strange looking filename '{filename}'.")
        else:
            objname = filename[0:-2]+".o"
            with open(filename,"r") as infile:
                inlines = infile.readlines()
                outvals = do_assembly( filename, inlines )
                if outvals != None:
                    with open(objname,"w") as outfile:
                        for outval in outvals:
                            outfile.write(f"{outval:04x}\n")
    return( 0 )


# Remove leading and trailing whitespace, comments, and reduce
# all inline whitespace to a single space
def strip_completely( line ):
    line2 = line.strip().split('#')[0]
    res = ""
    was_ws = False
    for c in line2:
        if c.isspace():
            if was_ws:
                continue
            else:
                res += " "
                was_ws = True
        else:
            res += c
            was_ws = False
    return res


def get_regnum(rstr):
    return int(rstr[1:])

def get_cond(cstr):
    seen_pos = False
    seen_neg = False
    f = 0
    for c in cstr:
        i = {
            "a": (0,False),
            "A": (0,True),
            "e": (1,False),
            "E": (1,True),
            "g": (2,False),
            "G": (2,True),
        }.get(c,None)
        if i:
            if i[1]:
                seen_neg = True
            else:
                seen_pos = True
            f |= 1<<i[0]
        else:
            return None
    if seen_pos and seen_neg:
        return None
    if not ( seen_pos or seen_neg ):
        return None
    if seen_pos:
        f |= 16
    return f

def do_assembly( filename, lines ):
    target_address = 0
    labels = {}
    relocs = []
    outvals = []
    for rawline in lines:
        line = strip_completely(rawline)
        if line=="":
            continue
        if line[0]=='.':          # Directive
            parts = line.split(" ")
            if parts[0] == ".word":
                val = 0
                try:
                    val = int(parts[1],0) % 65536
                except:
                    relocs.append((target_address,"word",parts[1]))
                outvals.append(val)
                target_address += 1
            elif parts[0] == ".org":
                new_address = int(parts[1],0) % 65536
                if new_address < target_address:
                    print(f"Unable to process OoO orgs. Skipping output for '{filename}'.")
                    return None
                while target_address < new_address:
                    outvals.append(0)
                    target_address+=1
            else:
                print(f"Unknown directive '{parts[0]}'. Skipping output for '{filename}'.")
                return None
        elif line[-1] == ':':    # Label
            labels[line[0:-1]] = target_address
        else:                   # An instruction
            splpos = line.find(" ")
            if splpos == -1:
                parts = [line]
            else:
                parts = [line[0:splpos],line[splpos+1:]]
            instr = parts[0].split(".")
            if len(parts) > 1:
                ops = [x.strip() for x in parts[1].split(",")]
            else:
                ops = []
            if len(instr) == 1:
                instr.append("a")
            val = 0
            if instr[0] == "halt":
                val = 0
            elif instr[0] == "const":
                r = get_regnum(ops[0])
                c = 0
                try:
                    c = int(ops[1],0) % 256
                except:
                    relocs.append((target_address,"lowbyte",ops[1]))
                val = (9<<11) | (r<<8) | c
            elif instr[0] == "out":
                r1 = get_regnum(ops[0])
                r2 = get_regnum(ops[1])
                cc = get_cond(instr[1])
                if not cc:
                    print(f"Failed to parse condition code '{instr[1]}'. Skipping output for '{filename}'")
                    return None
                val = (8<<11) | (r1<<8) | (r2<<5) | cc
            elif instr[0] in ["cmp","jp","add","sub"]:
                r1 = get_regnum(ops[0])
                r2 = get_regnum(ops[1])
                cc = get_cond(instr[1])
                if not cc:
                    print(f"Failed to parse condition code '{instr[1]}'. Skipping output for '{filename}'")
                    return None
                oc = {"cmp":7,"jp":1,"add":5,"sub":6}[instr[0]]
                val = (oc<<11) | (r1<<8) | (r2<<5) | cc
            else:
                print(f"Unknown opcode '{instr[0]}'. Skipping output for '{filename}'.")
                return None
            if val != None:
                outvals.append(val)
                target_address += 1
    for (tgt,mode,valt) in relocs:
        if valt not in labels:
                print(f"Attempt to use label '{valt}' not resolved. Skipping output for '{filename}'")
                return None
        val = labels[valt]
        if mode=="word":
            outvals[tgt] = val
        elif mode=="lowbyte":
            outvals[tgt] = (outvals[tgt]&0xff00)|val
        else:
            print(f"Failed to apply reloc '{mode}' using '{valt}'. Skipping output for '{filename}'")
            return None
    return outvals

work()

