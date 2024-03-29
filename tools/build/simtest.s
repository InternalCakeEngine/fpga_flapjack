loads:
  sub 2, sp
  st  ct, sp[2]
  const hi(23), r1
  const lo(23), r1
  st  r1, sp[0]
  ld  sp[0], r1
  mov  r1, r0
  ld  sp[2], ct
  ret 2
