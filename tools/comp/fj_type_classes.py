# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# These are the types that are used during compilation. I.e. not the
# same ones (at least not necessaryily the same ones
#

# NOTES:
#

from fj_parsed_classes import *

class BaseType():
    def __init__(self,name):
        self.name = name
        self.size = None

    def __eq__(self,other):
        return False

    def __str__(self):
        return self.name

class SimpleType(BaseType):
    def __init__(self,name):
        super().__init__(name)
        self.size = 1

    def __str__(self):
        return f"{self.name}"

    def __eq__(self,other):
        return isinstance(other,SimpleType) and self.name == other.name

class StructType(BaseType):
    def __init__(self,name):
        super().__init__(name)
        self.elems = []

    def __eq__(self,other):
        return self.elems == other.elems

    def __str__(self):
        return f"struct {self.name} {{ {''.join([str(e)+'; ' for e in self.elems])} }}"

class StructTypeElem(): # Not a type by itself, just part of a struct.
    def __init__(self,name,utype,offset):
        self.name = name
        self.utype = utype
        self.offset = offset
        self.size = None

    def __eq__(self,other):
        return self.utype==other.utype and self.name==other.name

    def __str__(self):
        return f"{self.name}->{self.utype}"

class RefType():
    def __init__(self,wrapped):
        self.wrapped = wrapped
        self.size = 1

    def __eq__(self,other):
        return isinstance(other,RefType) and self.wrapped == other.wrapped

    def __str__(self):
        return f"ref({self.wrapped})"

