.org 0

# r0 - Value being incremented
# r2 - branch target for loop continue
# r3 - branch target for restarting loop
# r5 - temporary copy of r0
# r6 - temporary for digit lookup
# r7 - screen coordinates
# r8 - output loop counter
# r9 - nybble loop target
# r11 - temp copy of r5
# r12 - screen location delta

	const	r0, 0
	const	r3, looptop
	const	r2, incandloop
	const	r9, nextnib
	const	r12, 255
	const	r12, 0

	# Start of printing
looptop:
	mov	0, r8
	mov	r0, r5		# Make a working copy
	const	r7, 42		# Reset screen address
	const	r7, 10
nextnib:
	mov	r5, r11
	shr	4, r5		# Shift down by a nybble
	and	0xf, r11		# Just the bottom nybblet
	const	r6, 0
	const	r6, digitlut
	add	r11, r6
	ld	r6, r6
	out	r6, r7
	add	r12, r7
	add	1, r8
	cmp	4, r8
	jp.e	r2, r9

incandloop:
	add	1, r0
	jp.a	r3, r3

digitlut:
	.word	48
	.word	49
	.word	50
	.word	51
	.word	52
	.word	53
	.word	54
	.word	55
	.word	56
	.word	57
	.word	65
	.word	66
	.word	67
	.word	68
	.word	69
	.word	70
