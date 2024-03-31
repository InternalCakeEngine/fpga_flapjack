# 
# This file is part of the Flapjack instruction level simulator
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk
#

import sys

mem = []
regs = []

IP = 15
SP = 14
FL = 13
CT = 12

def init():
    global mem
    global regs
    mem = [ 0 for i in range(0,65536) ]
    regs = [0 for i in range(0,16) ]
    regs[SP] = 65535

def start( infilename ):
    init()
    print(f"Memory words: {len(mem)}")
    print(f"Register words: {len(regs)}")
    with open(infilename,"r") as infile:
        inlines = infile.readlines()
    for n,inline in enumerate(inlines):
        mem[n] = int(inline.strip(),16)&65535
    work()


def work():
    global mem
    global regs
    running = True
    while running:
        instr = mem[regs[IP]]&65535
        prestr = f"{regs[IP]:04x} -> {instr:04x}"
        opcode = instr>>12
        op1_raw = (instr>>8)&15
        op2_raw = (instr>>4)&15
        op1_mode = (instr>>3)&1
        opindex = instr&7
        op1 = regs[op1_raw]&65535
        op2 = regs[op2_raw]&65535
        ccs = (instr>>3)&1
        cc = (instr&7)
        condtrue = (cc&(regs[FL]|1)&7)==cc if (ccs==1) else (cc&((~(regs[FL]|1))&7))==cc

        inhibit_step = False
        if opcode==0:       #  nop
            if op1_raw == 1:
                # Call
                rmask = instr&255;
                for b in range(0,8):
                    if (rmask&(1<<b))!=0:
                        mem[regs[SP]] = regs[b]
                        regs[SP] -= 1
                regs[CT] = regs[IP]+1
                regs[IP] = op2
                inhibit_step = True
            elif op1_raw == 2:
                # Save high
                rmask = instr&255;
                for b in range(0,8):
                    if (rmask&(1<<b))!=0:
                        mem[regs[SP]] = regs[b+8]
                        regs[SP] -= 1
            elif op1_raw == 3:
                # Return
                regs[SP] = (regs[SP]&65535)+(instr&255);
                regs[IP] = regs[CT]
                inhibit_step = True
            else:
                running = False
        elif opcode==1:     #  jp      Jump            Jump to O1 if flag conditions are true else to O2
            regs[IP] = op1 if condtrue else op2
            inhibit_step = True
        elif opcode==2:     #  br      Branch          Jump to ip+const (const is bits 7..0 sign extended.
            #print(f"Branch at {regs[IP]} codetrue={condtrue}, ccs={ccs}, cc={cc}")
            if condtrue:
                c = ((instr>>4)&255)
                if c<128:
                    regs[IP] = (regs[IP]+c)&65535
                else:
                    regs[IP] = (regs[IP]-(256-c))&65535
                inhibit_step = True
            pass
        elif opcode==3:     #  ld      Load            Read from memory address O1 into O2
            regs[op2_raw] = op1_raw if op1_mode else mem[(op1+opindex)&65535]
        elif opcode==4:     #  st      Store           Write O1 into memory address O2
            mem[(op2+opindex)&65535] =  op1_raw if op1_mode else op1
        elif opcode==5:     #  add     Add             Add O1 to O2
            regs[op2_raw] = (regs[op2_raw] + ( op1_raw if op1_mode else op1 ))&65535
        elif opcode==6:     #  sub     Sub             Sub O1 from O2
            regs[op2_raw] = (regs[op2_raw] - ( op1_raw if op1_mode else op1 ))&65535
        elif opcode==7:     #  cmp     Compare         Compare O1 to O2
            v = regs[op2_raw] - ( op1_raw if op1_mode else op1 )
            regs[FL] = (regs[FL]&~15) | 1 | ( 2 if (v==0) else 0 ) | ( 4 if (v<0) else 0 )
        elif opcode==8:     #  out     Write to IO     Write O1 into IO address O2
            print(f"Output {op1:04x},{op2:02x}")
        elif opcode==9:     #  const   Load 8bits      Write to O1 0x00nnn
            regs[op1_raw] = ((op1<<8)|(instr&255))&65535
        elif opcode==10:    #  bits    logic ops
            if instr&7 == 0:
                regs[op2_raw] &= op1_raw if op1_mode else op1
            elif instr&7 == 1:
                regs[op2_raw] |= op1_raw if op1_mode else op1
            elif instr&7 == 2:
                regs[op2_raw] ^= op1_raw if op1_mode else op1
            elif instr&7 == 3:
                #print(f"Shift {regs[op2_raw]} left by {op1_raw if op1_mode else op1}, op1_mode={op1_mode}")
                regs[op2_raw] <<= op1_raw if op1_mode else op1
            elif instr&7 == 4:
                regs[op2_raw] >>= op1_raw if op1_mode else op1
        elif opcode==11:    #  mov     Reg-reg move    Copy o1 into o2
            regs[op2_raw] = op1_raw if op1_mode else op1
        elif opcode==12:    #  shr     Shift right     Shift o2 right by o1 bits
            regs[op2_raw] >>= op1_raw if op1_mode else op1
        if not inhibit_step:
            regs[IP] += 1
        print(f"{prestr}  regs  "+"  ".join( [ f"{n}:{(x&65535):04x}" for n,x in enumerate(regs) ] ))

    print("Exit with:")
    print("  ".join( [ f"{n}:{(x&65535):04x}" for n,x in enumerate(regs) ] ))

start( sys.argv[1] )

