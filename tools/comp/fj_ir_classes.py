# A location descriptor.
# itype is one of "l" (local), "c" (constant), "nop" (nothing), or "sa" (single assignment)
# iden is dependent on the itype but is generally an int
class IrLoc():
    def __init__(self,itype,iden):
        self.itype = itype
        self.iden = iden

    def pretty(self):
        return f"{self.itype}({self.iden})"

# A single IR operation.
# op is a pseudo opcode: load, store, add, etc
# srcs is a list of IrLocs (semantics according to op, but always used)
# dst is a single IrLoc (semantics according to op, but always mutated)
class IrStep():
    def __init__(self,op,srcs,dst):
        self.op = op
        self.srcs = srcs
        self.dst = dst

    def pretty(self):
        return f"{self.op}("+(",".join([src.pretty() for src in self.srcs]))+")->"+self.dst.pretty()
