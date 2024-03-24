# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Create home locations for all the params of locals.
#

# NOTES:
#    Currently no concession for return addresses.

from fj_parsed_classes import *

def fj_layout( proot ):
    for entity in proot:
        if isinstance(entity,FunctionDef):
            _layout_function( entity )
    return proot


def _layout_function( fd ):
    initial_offset = 0
    for param in fd.params:
        param.offset = initial_offset
        initial_offset += 1
    _do_layout( fd.code, fd.params, initial_offset )

def _do_layout( cb, parentcb, offset ):
    cb.offset = offset
    cb.parent = parentcb
    for line in cb.lines:
        line.set_cb(cb)
        if isinstance(line,LocalVar):
            line.offset = offset
            offset += 1
        elif isinstance(line,CodeBlock):
            _do_layout( line, cb, offset )
        elif isinstance(line,Assignment):
            pass
        elif isinstance(line,Return):
            pass
        else:
            print(f"Met unknown linetype in layout: {line}")
            exit(1)



