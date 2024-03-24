# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Front end and driver for the compiler.
#

from fj_parser import fj_parser
from fj_layout import fj_layout
from fj_compile import fj_compile

def main():
    with open("test.oats","r") as infile:
        inlines = "\n".join(infile.readlines())
    objform = fj_parser( inlines )
    fj_layout( objform )   # Setup home locations for params and locals
    fj_compile( objform )  # Transform to assembly

if __name__ == '__main__':
    main()





