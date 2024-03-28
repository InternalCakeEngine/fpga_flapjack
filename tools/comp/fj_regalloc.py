# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Allocate registers to SA locations, inject spills and
# initial stack allocation.
#

from fj_ir_classes import *


def fj_regalloc( func_list ):
    for func in func_list:
        func["ir"] = _regalloc_func( func )

def _regalloc_func( func ):

    # Expand the IR into a list of dicts we can add attributes to and
    # subsequently modify in place.
    steplist = []
    for ir in func["ir"]:
        steplist.append( {"ir":ir} )

    _build_live_list( steplist )
    _reduce_to_2op( steplist )
    spill_delta = _to_real_reg( steplist, func["next_local"] )
    #spill_delta = 0
    func["next_local"] += spill_delta

    return steplist


# Build the raw ir into a live list for SA targets.
# This also eliminates SA writes that are never read.
def _build_live_list( steplist ):

    proglist = []
    livelist = set()
    lastreads = {}

    for index, step in enumerate(steplist):
        dst = step["ir"].dst
        if dst and dst.itype == "sa":
            livelist.add(dst.iden)
        step["livesa"] = livelist.copy()
        for src in step["ir"].srcs:
            if src.itype == "sa":
                lastreads[src.iden] = index

    for index, step in enumerate(steplist):
        dst = step["ir"].dst
        if dst and dst.itype == "sa":
            if index >= lastreads[dst.iden]:
                dst.itype = 'nop'
                dst.iden = None
        new_set = set()
        for sa in step["livesa"]:
            if index <= lastreads[sa]:
                new_set.add(sa)
        step["livesa"] = new_set

# Optimisation: for a 2-op machine eliminate cases where f(a,b)->c could
# be expressed as f(a,b)->b because b ceases to be live. Otherwise we'll need
# to insert extra moves and temp registers at code generation.
# When we find this case, we renumber the SA locations to hide the extra SA.
# For now we do this per-op, but classes of ops will be a better route in the future.
def _reduce_to_2op( steplist ):

    renumbernotes = {}
    step = None
    for nextstep in steplist:
        if step == None:
            step = nextstep
            continue
        # Do the renumber first.
        dst = step["ir"].dst
        if dst and dst.itype == "sa":
            dst.iden = renumbernotes.get(dst.iden,dst.iden)
        for src in step["ir"].srcs:
            if src.itype == "sa":
                src.iden = renumbernotes.get(src.iden,src.iden)
        livecopy = set(step["livesa"])
        for sa in livecopy:
            if sa in renumbernotes:
                step["livesa"].remove(sa)
        # Then mutate on a per-op basis.
        if step["ir"].op == "add":
            if step["ir"].srcs[1].itype=="sa" and step["ir"].dst.itype=="sa" and step["ir"].srcs[1].iden not in nextstep["livesa"]:
                renumbernotes[step["ir"].dst.iden] = step["ir"].srcs[1].iden
                step["livesa"].remove( step["ir"].dst.iden )
                step["ir"].dst.iden = step["ir"].srcs[1].iden

        # This must always happen i.e. no continue-ing.
        step = nextstep


# Replace SA references to real register number (ir changes from "sa" to "r".
# It relies on the principle that once an SA is out of the liveset, it never returns.
# There is knowlege of the target system embedded in here, which should really be externalised.
def _to_real_reg( steplist, next_local_index ):

    spill_delta = 0

    regs = ["r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12"]

    # Mapping from SA to reg and remaining free regs.
    smap = {}
    freeregs = regs.copy()

    for step in steplist:
        # First, unallocate any registers no longer needed.
        newmap = {}
        for sa in smap:
            if sa in step["livesa"]:
                newmap[sa] = smap[sa]
            else:
                freeregs = [smap[sa]]+freeregs
                #freeregs.append(smap[sa])
        smap = newmap
        for item in step["ir"].srcs+[step["ir"].dst]:
            if item and item.itype=="sa":
                sa = item.iden
                if sa not in smap:
                    newreg = "ERROR"
                    if regs!=[]:
                        newreg = freeregs[0]
                        freeregs = freeregs[1:]
                    else:
                        # Need to spill TBD
                        newreg = "ERROR"
                    smap[item.iden] = newreg
                item.itype="r"
                item.iden = smap[sa]

    return spill_delta

