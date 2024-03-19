.org 0
	const	r1, resetchar
	const	r2, 0x1
	const	r3, 0x5C
	const	r4, nextchar
resetchar:
	const	r0, 0x41
nextchar:
	out	r0, r1
	add	r2, r0
	cmp	r0, r3
	jp.e	r1, r4
	halt


