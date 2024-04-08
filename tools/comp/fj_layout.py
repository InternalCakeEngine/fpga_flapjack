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
    _do_layout( fd.code, fd.params, -1 )
    #print(f"Stack extent of func {fd.name} is {fd.code.stackextent}")
    fd.stackextent = fd.code.stackextent
    param_offset = len(fd.params)
    for param in fd.params:
        param.offset = param_offset
        param_offset -= 1

def _do_layout( cb, parentcb, offset ):
    cb.parent = parentcb
    local_extent = 0
    for line in cb.lines:
        if isinstance(line,LocalVar):
            local_extent += line.type.size
    cb.stackextent = local_extent
    local_offset = 0
    for line in cb.lines:
        line.set_cb(cb)
        if isinstance(line,LocalVar):
            line.offset = (offset+1)-(local_extent-local_offset)
            #print(f"Total offset of {line.name} is {line.offset} (local_extent={local_extent}")
            local_offset += line.type.size
        elif isinstance(line,CodeBlock):
            _do_layout( line, cb, offset-local_extent )
        elif isinstance(line,Assignment):
            pass
        elif isinstance(line,WhileLoop):
            _do_layout( line.code_block, cb, offset-local_extent )
        elif isinstance(line,IfElse):
            _do_layout( line.code_block_if, cb, offset-local_extent )
            if line.code_block_else:
                _do_layout( line.code_block_else, cb, offset-local_extent )
        elif isinstance(line,Return):
            pass
        else:
            print(f"Met unknown linetype in layout: {line}")
            exit(1)

