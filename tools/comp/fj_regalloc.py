# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Allocate registers to SA locations, inject spills and
# initial stack allocation.
#

from fj_ir_classes import *


def fj_regalloc( ir_list ):
    for func in ir_list:
        print(f"Function: {func['name']}")
        func["ir"] = _regalloc_func( func["ir"] )
        for step in func["ir"]:
            print(step["ir"].pretty(),step["livesa"])

def _regalloc_func( irin ):

    # Expand the IR into a list of dicts we can add attributes to and
    # subsequently modify in place.
    steplist = []
    for ir in irin:
        steplist.append( {"ir":ir} )

    _build_live_list( steplist )
    _reduce_to_2op( steplist )

    return steplist


# Build the raw ir into a live list for SA targets.
# This also eliminates SA writes that are never read.
def _build_live_list( steplist ):

    proglist = []
    livelist = set()
    lastreads = {}

    for index, step in enumerate(steplist):
        dst = step["ir"].dst
        if dst.itype == "sa":
            livelist.add(dst.iden)
        step["livesa"] = livelist.copy()
        for src in step["ir"].srcs:
            if src.itype == "sa":
                lastreads[src.iden] = index

    for index, step in enumerate(steplist):
        dst = step["ir"].dst
        if dst.itype == "sa":
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
        if dst.itype == "sa":
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

