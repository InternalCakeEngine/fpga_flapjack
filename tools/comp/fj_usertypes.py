# This file is part of the Flapjack language compiler
# (c) 2024 Martin Young
# Contact: martin@endotether.org.uk

#
# Build (and store here) user defined types.
#

# NOTES:
#

from fj_parsed_classes import *
from fj_type_classes import *

# Dictionary of defined types (UserTypes)
user_types = {}

def fj_buildtypes( proot ):
    # First build list of user types so we can look them up.
    for entity in proot:
        if isinstance(entity,StructDef):
            user_types[entity.name] = "exists";
    # If we supported arbitrary typedefs we'd do that here too.
    # Grovel over all the source, changing parsed structures to working structures.
    for entity in proot:
        if isinstance(entity,FunctionDef):
            entity.return_type = _replace_typing(entity.return_type)
            _replace_typing_in_codeblock( entity.code )
        elif isinstance(entity,LocalVar):
            _replace_typing_in_local( entity )
        elif isinstance(entity,StructDef):
            _replace_typing_in_structdef( entity )
    # Then actually construct any user types.
    for entity in proot:
        if isinstance(entity,StructDef):
            new_struct = _build_struct( entity )
            user_types[new_struct.name] = new_struct

def _replace_typing_in_codeblock( cb ):
    for line in cb.lines:
        if isinstance(line,LocalVar):
            line.type=_replace_typing(line.type)
        elif isinstance(line,IfElse):
            _replace_typing_in_codeblock(line.code_block_if)
            _replace_typing_in_codeblock(line.code_block_else)
        elif isinstance(line,WhileLoop):
            _replace_typing_in_codeblock(line.code_block)
        elif isinstance(line,Assignment):
            _replace_typing_in_expression(line.exp)

def _replace_typing_in_expression( exp ):
    if isinstance(exp,ExpOp):
        pass
    if isinstance(exp,ExpNode):
        if exp.operator == ExpNode.IDEN:
            exp.utype = _find_type_of_identifier(exp.operands[0]);
        elif exp.operator == ExpNode.LIT:
            exp.utype = SimpleType("int16")
        elif exp.operator == ExpNode.CALL:
            exp.utype = _find_type_of_function(exp.operands[0]);
            for o in exp.operands[1:]:
                _replace_typing_in_expression(o);
        elif exp.operator == ExpNode.EMPTY:
            exp.utype = SimpleType("empty")
    elif isinstance(exp,ExpSubsript):
        for o in exp.sublist:
            _replace_typing_in_expression(o);
    elif isinstance(exp,ExpRef):
        _replace_typing_in_expression(exp.exp)
        exp.utype = RefType(exp.exp.utype)
        pass

def _replace_typing_in_structdef( sd ):
    for elem in sd.elemlist:
        elem.elemtype = _replace_typing(elem.elemtype)

def _replace_typing( parsed_type ):
    print(f"Try to replace {type(parsed_type)} {parsed_type}")
    if isinstance(parsed_type,SimpleTypeUse):
        return SimpleType(parsed_type.typename)
    elif isinstance(parsed_type,RefTypeUse):
        return RefType( _replace_typing(parsed_type.warpped) )
    elif isinstance(parsed_type,UserTypeUse):
        for utk in user_types:
            print(f"parsed_type: {type(parsed_type)} {parsed_type}")
            if utk == parsed_type.typename:
                return user_types[utk]
    else:
        print(f"Failed to look up user type {parsed_type.name}.")
        exit(1)

def _build_struct( td ):
    new_struct = StructType( td.name )
    offset = 0
    for elem in td.elemlist:
        if elem.elemtype == SimpleType("int16"):
            new_struct.elems.append( StructTypeElem(elem.name,elem.elemtype,offset ) )
            offset += 1
        elif elem.elemtype == RefType(SimpleType("int16")):
            new_struct.elems.append( StructTypeElem(elem.name,elem.elemtype,offset ) )
            offset += 1
        else:
            print(f"Typeof elem.elemtype {type(elem.elemtype)}")
            print(f"Unable to add type {elem.elemtype} to struct {td.name}")
            exit(1)
    return new_struct

