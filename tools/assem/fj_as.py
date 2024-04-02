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
    rstr = rstr[:-1] if rstr[-1] in ["+","-"] else rstr
    if rstr[:2]=="ip":
        return 15
    elif rstr[:2]=="sp":
        return 14
    elif rstr[:2]=="fl":
        return 13
    elif rstr[:2]=="ct":
        return 12
    endloc = rstr.index('[') if '[' in rstr else None
    return int(rstr[1:endloc])

def get_subindex(rstr):
    if '[' in rstr:
        return int(rstr[rstr.index('[')+1:-1])
    return 0

def get_smallvalue(vstr):
    return int(vstr,0)%0x10

def get_opmode(rstr):
    if rstr[0]=='r' or rstr[:2] in ["ip","fl","sp","ct"]:
        return 0
    else:
        return 1

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
        f |= 8
    return f

fmt1 = {
    "jp":1,
}

fmt2 = {
    "ld":3,
    "st":4,
    "add":5,
    "sub":6,
    "cmp":7,
    "out":8,
    "and":10,
    "or":10,
    "xor":10,
    "shr":10,
    "shl":10,
    "mov":11,
}

fmt3 = {
    "const": 9,
}

# All the main opcodes are zero. Subcode are given here.
fmt4 = {
    "nop": 0,
    "call": 1,
    "saveh": 2,
    "ret": 3
}

fmt5 = {
    "br":2,
}

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
            elif instr[0] in fmt1:
                r1 = get_regnum(ops[0])
                r2 = get_regnum(ops[1])
                cc = get_cond(instr[1])
                if not cc:
                    print(f"Failed to parse condition code '{instr[1]}'. Skipping output for '{filename}'")
                    return None
                oc = fmt1[instr[0]]
                val = (oc<<12) | (r1<<8) | (r2<<4) | cc
            elif instr[0] in fmt2:
                i=0
                a = get_opmode(ops[0])
                if a==1:
                    r1 = get_smallvalue(ops[0])
                else:
                    r1 = get_regnum(ops[0])
                r2 = get_regnum(ops[1])
                if instr[0] == "st":
                    i = get_subindex(ops[1])
                elif instr[0] == "ld":
                    i = get_subindex(ops[0])
                elif instr[0] in ["and","or","xor","shl","shr"]:
                    i = {"and":0,"or":1,"xor":2,"shl":3,"shr":4}[instr[0]]
                oc = fmt2[instr[0]]
                val = (oc<<12) | (r1<<8) | (r2<<4) | (a<<3) | (i&7)
            elif instr[0] in fmt3:
                r = get_regnum(ops[1])
                c = 0
                cshift = 0
                if ops[0][0:3]=="hi(":
                    opstr = ops[0][3:-1]
                    cshift = 8
                elif ops[0][0:3]=="lo(":
                    opstr = ops[0][3:-1]
                else:
                    opstr = ops[0]
                try:
                    c = ( int(opstr,0)>>cshift ) % 256
                except:
                    if cshift==8:
                        relocs.append((target_address,"highbyte",ops[0]))
                    else:
                        relocs.append((target_address,"lowbyte",ops[0]))
                oc = fmt3[instr[0]]
                val = (oc<<12) | (r<<8) | c
            elif instr[0] in fmt4:
                opcode = 0
                subcode = fmt4[instr[0]]
                if instr[0] == "call":
                    c = get_regnum(ops[0])<<4
                elif instr[0] == "nop":
                    c=0
                else:
                    c = int(ops[0],0)&255
                val = (opcode<<12) | (subcode<<8) | c
            elif instr[0] in fmt5:
                opstr = ops[0]
                try:
                    c = int(opstr,0)
                    if c>127 or c<-128:
                        print(f"Branch out of range. {c}")
                        return None
                except:
                    relocs.append((target_address,"addrdelta",ops[0]))
                cc = get_cond(instr[1])
                if not cc:
                    print(f"Failed to parse condition code '{instr[1]}'. Skipping output for '{filename}'")
                    return None
                oc = fmt5[instr[0]]
                val = (oc<<12) | (c<<4) | cc
            else:
                print(f"Unknown opcode '{instr[0]}'. Skipping output for '{filename}'.")
                return None
            if val != None:
                outvals.append(val)
                target_address += 1

    # Apply local relocations.
    for (tgt,mode,full_valt) in relocs:
        if full_valt[0:3]=="hi(" or full_valt[0:3]=="lo(":
            valt = full_valt[3:-1]
        else:
            valt = full_valt
        if valt not in labels:
            print(f"Attempt to use label '{valt}' not resolved. Skipping output for '{filename}'")
            return None
        val = labels[valt]
        if mode=="word":
            outvals[tgt] = val
        elif mode=="lowbyte":
            outvals[tgt] = (outvals[tgt]&0xff00)|(val&0xff)
        elif mode=="highbyte":
            outvals[tgt] = (outvals[tgt]&0xff00)|((val>>8)&0xff)
        elif mode=="addrdelta":
            outvals[tgt] = (outvals[tgt]&0xf00f)|(((val-tgt)&0xff)<<4)
        else:
            print(f"Failed to apply reloc '{mode}' using '{valt}'. Skipping output for '{filename}'")
            return None
    return outvals

work()

