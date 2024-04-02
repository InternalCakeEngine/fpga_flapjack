main:
  sub 1, sp
  st  ct, sp[0]
loc_0:
  const hi(1), r1
  const lo(1), r1
  cmp 0, r1
  br.e loc_1
  sub 0, sp
  const hi(work), r0
  const lo(work), r0
  call r0
  add 0, sp
  br.a loc_0
loc_1:
  ld sp[0], ct
  ret 1
work:
  sub 2, sp
  st  ct, sp[1]
  const hi(32), r1
  const lo(32), r1
  st  r1, sp[0]
loc_9:
  ld  sp[0], r1   # stack_offset=1, src.iden=-1
  const hi(128), r2
  const lo(128), r2
  mov  1, r3
  cmp r1, r2
  br.GE loc_2
  mov  0, r3
loc_2:
  cmp 0, r3
  br.e loc_10
  sub 1, sp
  const hi(0), r3
  const lo(0), r3
  st  r3, sp[0]
loc_7:
  ld  sp[0], r3   # stack_offset=2, src.iden=-2
  const hi(30), r2
  const lo(30), r2
  mov  1, r1
  cmp r3, r2
  br.GE loc_3
  mov  0, r1
loc_3:
  cmp 0, r1
  br.e loc_8
  sub 1, sp
  const hi(0), r1
  const lo(0), r1
  st  r1, sp[0]
loc_5:
  ld  sp[0], r1   # stack_offset=3, src.iden=-3
  const hi(80), r2
  const lo(80), r2
  mov  1, r3
  cmp r1, r2
  br.GE loc_4
  mov  0, r3
loc_4:
  cmp 0, r3
  br.e loc_6
  sub 1, sp
  ld  sp[3], r3   # stack_offset=4, src.iden=-1
  ld  sp[1], r2   # stack_offset=4, src.iden=-3
  ld  sp[2], r1   # stack_offset=4, src.iden=-2
  sub 3, sp
  st r3, sp[2]
  st r2, sp[1]
  st r1, sp[0]
  const hi(write_char), r0
  const lo(write_char), r0
  call r0
  add 3, sp
  ld  sp[1], r1   # stack_offset=4, src.iden=-3
  const hi(1), r2
  const lo(1), r2
  add  r1, r2
  st  r2, sp[1]
  add 1, sp
  br.a loc_5
loc_6:
  ld  sp[1], r2   # stack_offset=3, src.iden=-2
  const hi(1), r1
  const lo(1), r1
  add  r2, r1
  st  r1, sp[1]
  add 1, sp
  br.a loc_7
loc_8:
  ld  sp[1], r1   # stack_offset=2, src.iden=-1
  const hi(1), r2
  const lo(1), r2
  add  r1, r2
  st  r2, sp[1]
  add 1, sp
  br.a loc_9
loc_10:
  ld sp[1], ct
  ret 2
write_char:
  sub 2, sp
  st  ct, sp[1]
  ld  sp[3], r1   # stack_offset=1, src.iden=2
  const hi(8), r2
  const lo(8), r2
  shl  r2, r1
  ld  sp[2], r2   # stack_offset=1, src.iden=1
  or  r2, r1
  st  r1, sp[0]
  ld  sp[4], r1   # stack_offset=1, src.iden=3
  ld  sp[0], r2   # stack_offset=1, src.iden=-1
  sub 2, sp
  st r1, sp[1]
  st r2, sp[0]
  const hi(_asm_out), r0
  const lo(_asm_out), r0
  call r0
  add 2, sp
  ld sp[1], ct
  ret 2
_asm_out:
  ld sp[0], r10
  ld sp[1], r11
  out r11, r10
  ret 0
