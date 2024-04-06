# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Build (and store here) user defined types.
#

# NOTES:
#

from fj_parsed_classes import *

class UserTypeElem():
    def __init__(self,name,utype,offset):
        self.name = name
        self.utype = utype
        self.offset = offset

    def __str__(self):
        return f"{self.name}->{self.utype}"

class UserType():
    def __init__(self,name):
        self.name = name
        self.utype = "struct"
        self.elems = []

    def __str__(self):
        return f"struct {self.name} {{ {''.join([str(e)+'; ' for e in self.elems])} }}"

# Dictionary of defined types (UserTypes)
user_types = {}

def fj_buildtypes( proot ):
    for entity in proot:
        if isinstance(entity,StructDef):
            new_struct = _build_struct( entity )
            user_types[new_struct.name] = new_struct
    return proot


def _build_struct( td ):
    new_struct = UserType( td.name )
    offset = 0
    for elem in td.elemlist:
        if elem.elemtype == SimpleType("int16"):
            new_struct.elems.append( UserTypeElem(elem.name,elem.elemtype,offset ) )
            offset += 1
        elif elem.elemtype == RefType(SimpleType("int16")):
            new_struct.elems.append( UserTypeElem(elem.name,elem.elemtype,offset ) )
            offset += 1
        else:
            print(f"Unable to add type {elem.elemtype} to struct {td.name}")
            exit(1)
    return new_struct

