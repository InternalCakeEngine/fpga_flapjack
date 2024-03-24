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
        print(f"Offset of param {param.name} is {param.offset}")
    _do_layout( fd.code, initial_offset )

def _do_layout( cb, offset ):
    cb.offset = offset
    for line in cb.lines:
        if isinstance(line,LocalVar):
            line.offset = offset
            print(f"Initial offset of {line.name} is {line.offset}")
            offset += 1
        elif isinstance(line,CodeBlock):
            _do_layout( line, offset )
        elif isinstance(line,Assignment):
            pass
        elif isinstance(line,Return):
            pass
        else:
            print(f"Met unknown linetype in layout: {line}")
            print(line.pretty())
            exit(1)



