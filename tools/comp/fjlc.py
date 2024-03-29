# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Front end and driver for the compiler.
#

import sys

from fj_parser import fj_parser
from fj_layout import fj_layout
from fj_compile import fj_compile
from fj_regalloc import fj_regalloc
from fj_toasm import fj_toasm

def main():
    with open(sys.argv[1],"r") as infile:
        inlines = "\n".join(infile.readlines())
    try:
        objform = fj_parser( inlines )
    except Exception as e:
        print("Exception parsing input.")
        print(e)
        exit(1)
    fj_layout( objform )                    # Setup home locations for params and locals
    ir_list = fj_compile( objform )         # Compile to IR
    fj_regalloc( ir_list )        # Allocated register, inject spills and stack allocs.
    out = fj_toasm( ir_list )               # Transform IR to assembly

if __name__ == '__main__':
    main()





