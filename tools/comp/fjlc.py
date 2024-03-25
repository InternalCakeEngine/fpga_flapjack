# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Front end and driver for the compiler.
#

from fj_parser import fj_parser
from fj_layout import fj_layout
from fj_compile import fj_compile
from fj_regalloc import fj_regalloc
from fj_toasm import fj_toasm

def main():
    with open("test.oats","r") as infile:
        inlines = "\n".join(infile.readlines())
    objform = fj_parser( inlines )
    fj_layout( objform )            # Setup home locations for params and locals
    ir = fj_compile( objform )      # Compile to IR
    ra = fj_regalloc( ir )          # Allocated register, inject spills and stack allocs.
    out = fj_toasm( ra )            # Transform IR to assembly

if __name__ == '__main__':
    main()





