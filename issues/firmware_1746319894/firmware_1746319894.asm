;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler
; Version 4.5.0 #15242 (Mac OS X ppc)
;--------------------------------------------------------
	.module firmware_1746319894
	
	.optsdcc -mmcs51 --model-small
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _main
	.globl _sprintf
	.globl _CY
	.globl _AC
	.globl _F0
	.globl _RS1
	.globl _RS0
	.globl _OV
	.globl _F1
	.globl _P
	.globl _PS
	.globl _PT1
	.globl _PX1
	.globl _PT0
	.globl _PX0
	.globl _RD
	.globl _WR
	.globl _T1
	.globl _T0
	.globl _INT1
	.globl _INT0
	.globl _TXD
	.globl _RXD
	.globl _P3_7
	.globl _P3_6
	.globl _P3_5
	.globl _P3_4
	.globl _P3_3
	.globl _P3_2
	.globl _P3_1
	.globl _P3_0
	.globl _EA
	.globl _ES
	.globl _ET1
	.globl _EX1
	.globl _ET0
	.globl _EX0
	.globl _P2_7
	.globl _P2_6
	.globl _P2_5
	.globl _P2_4
	.globl _P2_3
	.globl _P2_2
	.globl _P2_1
	.globl _P2_0
	.globl _SM0
	.globl _SM1
	.globl _SM2
	.globl _REN
	.globl _TB8
	.globl _RB8
	.globl _TI
	.globl _RI
	.globl _P1_7
	.globl _P1_6
	.globl _P1_5
	.globl _P1_4
	.globl _P1_3
	.globl _P1_2
	.globl _P1_1
	.globl _P1_0
	.globl _TF1
	.globl _TR1
	.globl _TF0
	.globl _TR0
	.globl _IE1
	.globl _IT1
	.globl _IE0
	.globl _IT0
	.globl _P0_7
	.globl _P0_6
	.globl _P0_5
	.globl _P0_4
	.globl _P0_3
	.globl _P0_2
	.globl _P0_1
	.globl _P0_0
	.globl _B
	.globl _ACC
	.globl _PSW
	.globl _IP
	.globl _P3
	.globl _IE
	.globl _P2
	.globl _SBUF
	.globl _SCON
	.globl _P1
	.globl _TH1
	.globl _TH0
	.globl _TL1
	.globl _TL0
	.globl _TMOD
	.globl _TCON
	.globl _PCON
	.globl _DPH
	.globl _DPL
	.globl _SP
	.globl _P0
	.globl _init_system
	.globl _delay_ms
	.globl _read_adc
	.globl _read_temperature
	.globl _init_uart
	.globl _uart_tx_char
	.globl _uart_tx_string
;--------------------------------------------------------
; special function registers
;--------------------------------------------------------
	.area RSEG    (ABS,DATA)
	.org 0x0000
_P0	=	0x0080
_SP	=	0x0081
_DPL	=	0x0082
_DPH	=	0x0083
_PCON	=	0x0087
_TCON	=	0x0088
_TMOD	=	0x0089
_TL0	=	0x008a
_TL1	=	0x008b
_TH0	=	0x008c
_TH1	=	0x008d
_P1	=	0x0090
_SCON	=	0x0098
_SBUF	=	0x0099
_P2	=	0x00a0
_IE	=	0x00a8
_P3	=	0x00b0
_IP	=	0x00b8
_PSW	=	0x00d0
_ACC	=	0x00e0
_B	=	0x00f0
;--------------------------------------------------------
; special function bits
;--------------------------------------------------------
	.area RSEG    (ABS,DATA)
	.org 0x0000
_P0_0	=	0x0080
_P0_1	=	0x0081
_P0_2	=	0x0082
_P0_3	=	0x0083
_P0_4	=	0x0084
_P0_5	=	0x0085
_P0_6	=	0x0086
_P0_7	=	0x0087
_IT0	=	0x0088
_IE0	=	0x0089
_IT1	=	0x008a
_IE1	=	0x008b
_TR0	=	0x008c
_TF0	=	0x008d
_TR1	=	0x008e
_TF1	=	0x008f
_P1_0	=	0x0090
_P1_1	=	0x0091
_P1_2	=	0x0092
_P1_3	=	0x0093
_P1_4	=	0x0094
_P1_5	=	0x0095
_P1_6	=	0x0096
_P1_7	=	0x0097
_RI	=	0x0098
_TI	=	0x0099
_RB8	=	0x009a
_TB8	=	0x009b
_REN	=	0x009c
_SM2	=	0x009d
_SM1	=	0x009e
_SM0	=	0x009f
_P2_0	=	0x00a0
_P2_1	=	0x00a1
_P2_2	=	0x00a2
_P2_3	=	0x00a3
_P2_4	=	0x00a4
_P2_5	=	0x00a5
_P2_6	=	0x00a6
_P2_7	=	0x00a7
_EX0	=	0x00a8
_ET0	=	0x00a9
_EX1	=	0x00aa
_ET1	=	0x00ab
_ES	=	0x00ac
_EA	=	0x00af
_P3_0	=	0x00b0
_P3_1	=	0x00b1
_P3_2	=	0x00b2
_P3_3	=	0x00b3
_P3_4	=	0x00b4
_P3_5	=	0x00b5
_P3_6	=	0x00b6
_P3_7	=	0x00b7
_RXD	=	0x00b0
_TXD	=	0x00b1
_INT0	=	0x00b2
_INT1	=	0x00b3
_T0	=	0x00b4
_T1	=	0x00b5
_WR	=	0x00b6
_RD	=	0x00b7
_PX0	=	0x00b8
_PT0	=	0x00b9
_PX1	=	0x00ba
_PT1	=	0x00bb
_PS	=	0x00bc
_P	=	0x00d0
_F1	=	0x00d1
_OV	=	0x00d2
_RS0	=	0x00d3
_RS1	=	0x00d4
_F0	=	0x00d5
_AC	=	0x00d6
_CY	=	0x00d7
;--------------------------------------------------------
; overlayable register banks
;--------------------------------------------------------
	.area REG_BANK_0	(REL,OVR,DATA)
	.ds 8
;--------------------------------------------------------
; internal ram data
;--------------------------------------------------------
	.area DSEG    (DATA)
_main_temp_str_10001_58:
	.ds 16
;--------------------------------------------------------
; overlayable items in internal ram
;--------------------------------------------------------
	.area	OSEG    (OVR,DATA)
	.area	OSEG    (OVR,DATA)
	.area	OSEG    (OVR,DATA)
;--------------------------------------------------------
; Stack segment in internal ram
;--------------------------------------------------------
	.area SSEG
__start__stack:
	.ds	1

;--------------------------------------------------------
; indirectly addressable internal ram data
;--------------------------------------------------------
	.area ISEG    (DATA)
;--------------------------------------------------------
; absolute internal ram data
;--------------------------------------------------------
	.area IABS    (ABS,DATA)
	.area IABS    (ABS,DATA)
;--------------------------------------------------------
; bit data
;--------------------------------------------------------
	.area BSEG    (BIT)
;--------------------------------------------------------
; paged external ram data
;--------------------------------------------------------
	.area PSEG    (PAG,XDATA)
;--------------------------------------------------------
; uninitialized external ram data
;--------------------------------------------------------
	.area XSEG    (XDATA)
;--------------------------------------------------------
; absolute external ram data
;--------------------------------------------------------
	.area XABS    (ABS,XDATA)
;--------------------------------------------------------
; initialized external ram data
;--------------------------------------------------------
	.area XISEG   (XDATA)
	.area HOME    (CODE)
	.area GSINIT0 (CODE)
	.area GSINIT1 (CODE)
	.area GSINIT2 (CODE)
	.area GSINIT3 (CODE)
	.area GSINIT4 (CODE)
	.area GSINIT5 (CODE)
	.area GSINIT  (CODE)
	.area GSFINAL (CODE)
	.area CSEG    (CODE)
;--------------------------------------------------------
; interrupt vector
;--------------------------------------------------------
	.area HOME    (CODE)
__interrupt_vect:
	ljmp	__sdcc_gsinit_startup
; restartable atomic support routines
	.ds	5
sdcc_atomic_exchange_rollback_start::
	nop
	nop
sdcc_atomic_exchange_pdata_impl:
	movx	a, @r0
	mov	r3, a
	mov	a, r2
	movx	@r0, a
	sjmp	sdcc_atomic_exchange_exit
	nop
	nop
sdcc_atomic_exchange_xdata_impl:
	movx	a, @dptr
	mov	r3, a
	mov	a, r2
	movx	@dptr, a
	sjmp	sdcc_atomic_exchange_exit
sdcc_atomic_compare_exchange_idata_impl:
	mov	a, @r0
	cjne	a, ar2, .+#5
	mov	a, r3
	mov	@r0, a
	ret
	nop
sdcc_atomic_compare_exchange_pdata_impl:
	movx	a, @r0
	cjne	a, ar2, .+#5
	mov	a, r3
	movx	@r0, a
	ret
	nop
sdcc_atomic_compare_exchange_xdata_impl:
	movx	a, @dptr
	cjne	a, ar2, .+#5
	mov	a, r3
	movx	@dptr, a
	ret
sdcc_atomic_exchange_rollback_end::

sdcc_atomic_exchange_gptr_impl::
	jnb	b.6, sdcc_atomic_exchange_xdata_impl
	mov	r0, dpl
	jb	b.5, sdcc_atomic_exchange_pdata_impl
sdcc_atomic_exchange_idata_impl:
	mov	a, r2
	xch	a, @r0
	mov	dpl, a
	ret
sdcc_atomic_exchange_exit:
	mov	dpl, r3
	ret
sdcc_atomic_compare_exchange_gptr_impl::
	jnb	b.6, sdcc_atomic_compare_exchange_xdata_impl
	mov	r0, dpl
	jb	b.5, sdcc_atomic_compare_exchange_pdata_impl
	sjmp	sdcc_atomic_compare_exchange_idata_impl
;--------------------------------------------------------
; global & static initialisations
;--------------------------------------------------------
	.area HOME    (CODE)
	.area GSINIT  (CODE)
	.area GSFINAL (CODE)
	.area GSINIT  (CODE)
	.globl __sdcc_gsinit_startup
	.globl __sdcc_program_startup
	.globl __start__stack
	.globl __mcs51_genXINIT
	.globl __mcs51_genXRAMCLEAR
	.globl __mcs51_genRAMCLEAR
	.area GSFINAL (CODE)
	ljmp	__sdcc_program_startup
;--------------------------------------------------------
; Home
;--------------------------------------------------------
	.area HOME    (CODE)
	.area HOME    (CODE)
__sdcc_program_startup:
	ljmp	_main
;	return from main will return to caller
;--------------------------------------------------------
; code
;--------------------------------------------------------
	.area CSEG    (CODE)
;------------------------------------------------------------
;Allocation info for local variables in function 'main'
;------------------------------------------------------------
;temperature   Allocated to registers r4 r5 r6 r7 
;temp_str      Allocated with name '_main_temp_str_10001_58'
;------------------------------------------------------------
;	./backend/backend/outputs/firmware_1746319894.c:27: void main(void) {
;	-----------------------------------------
;	 function main
;	-----------------------------------------
_main:
	ar7 = 0x07
	ar6 = 0x06
	ar5 = 0x05
	ar4 = 0x04
	ar3 = 0x03
	ar2 = 0x02
	ar1 = 0x01
	ar0 = 0x00
;	./backend/backend/outputs/firmware_1746319894.c:29: init_system();
	lcall	_init_system
;	./backend/backend/outputs/firmware_1746319894.c:32: init_uart();
	lcall	_init_uart
;	./backend/backend/outputs/firmware_1746319894.c:35: uart_tx_string("System initialized\r\n");
	mov	dptr,#___str_0
	mov	b, #0x80
	lcall	_uart_tx_string
;	./backend/backend/outputs/firmware_1746319894.c:42: while (1) {
00102$:
;	./backend/backend/outputs/firmware_1746319894.c:44: temperature = read_temperature();
	lcall	_read_temperature
	mov	r4, dpl
	mov	r5, dph
	mov	r6, b
	mov	r7, a
;	./backend/backend/outputs/firmware_1746319894.c:47: sprintf(temp_str, "Temp: %.1f C\r\n", temperature);
	push	ar4
	push	ar5
	push	ar6
	push	ar7
	mov	a,#___str_1
	push	acc
	mov	a,#(___str_1 >> 8)
	push	acc
	mov	a,#0x80
	push	acc
	mov	a,#_main_temp_str_10001_58
	push	acc
	mov	a,#(_main_temp_str_10001_58 >> 8)
	push	acc
	mov	a,#0x40
	push	acc
	lcall	_sprintf
	mov	a,sp
	add	a,#0xf6
	mov	sp,a
;	./backend/backend/outputs/firmware_1746319894.c:50: uart_tx_string(temp_str);
	mov	dptr,#_main_temp_str_10001_58
	mov	b, #0x40
	lcall	_uart_tx_string
;	./backend/backend/outputs/firmware_1746319894.c:54: delay_ms(1000);  // 1 second delay
	mov	dptr,#0x03e8
	lcall	_delay_ms
;	./backend/backend/outputs/firmware_1746319894.c:56: }
	sjmp	00102$
;------------------------------------------------------------
;Allocation info for local variables in function 'init_system'
;------------------------------------------------------------
;	./backend/backend/outputs/firmware_1746319894.c:61: void init_system(void) {
;	-----------------------------------------
;	 function init_system
;	-----------------------------------------
_init_system:
;	./backend/backend/outputs/firmware_1746319894.c:65: }
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'delay_ms'
;------------------------------------------------------------
;ms            Allocated to registers r6 r7 
;i             Allocated to registers r4 r5 
;j             Allocated to registers r2 r3 
;------------------------------------------------------------
;	./backend/backend/outputs/firmware_1746319894.c:70: void delay_ms(unsigned int ms) {
;	-----------------------------------------
;	 function delay_ms
;	-----------------------------------------
_delay_ms:
	mov	r6, dpl
	mov	r7, dph
;	./backend/backend/outputs/firmware_1746319894.c:72: for (i = 0; i < ms; i++) {
	mov	r4,#0x00
	mov	r5,#0x00
00107$:
	clr	c
	mov	a,r4
	subb	a,r6
	mov	a,r5
	subb	a,r7
	jnc	00109$
;	./backend/backend/outputs/firmware_1746319894.c:73: for (j = 0; j < 120; j++) {  // Adjust based on crystal frequency
	mov	r2,#0x78
	mov	r3,#0x00
00105$:
	dec	r2
	cjne	r2,#0xff,00138$
	dec	r3
00138$:
	mov	a,r2
	orl	a,r3
	jnz	00105$
;	./backend/backend/outputs/firmware_1746319894.c:72: for (i = 0; i < ms; i++) {
	inc	r4
	cjne	r4,#0x00,00107$
	inc	r5
	sjmp	00107$
00109$:
;	./backend/backend/outputs/firmware_1746319894.c:77: }
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'read_adc'
;------------------------------------------------------------
;channel       Allocated to registers 
;------------------------------------------------------------
;	./backend/backend/outputs/firmware_1746319894.c:82: unsigned int read_adc(unsigned char channel) {
;	-----------------------------------------
;	 function read_adc
;	-----------------------------------------
_read_adc:
;	./backend/backend/outputs/firmware_1746319894.c:86: return 512;  // Return mid-range value
	mov	dptr,#0x0200
;	./backend/backend/outputs/firmware_1746319894.c:87: }
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'read_temperature'
;------------------------------------------------------------
;adc_value     Allocated to registers 
;temperature   Allocated to registers r4 r5 r6 r7 
;------------------------------------------------------------
;	./backend/backend/outputs/firmware_1746319894.c:93: float read_temperature(void) {
;	-----------------------------------------
;	 function read_temperature
;	-----------------------------------------
_read_temperature:
;	./backend/backend/outputs/firmware_1746319894.c:98: adc_value = read_adc(0);
	mov	dpl, #0x00
	lcall	_read_adc
;	./backend/backend/outputs/firmware_1746319894.c:103: temperature = (adc_value * 0.488);  // Simplified calculation
	lcall	___uint2fs
	mov	r4, dpl
	mov	r5, dph
	mov	r6, b
	mov	r7, a
	push	ar4
	push	ar5
	push	ar6
	push	ar7
;	./backend/backend/outputs/firmware_1746319894.c:105: return temperature;
	mov	dptr,#0xdb23
	mov	b, #0xf9
	mov	a, #0x3e
	lcall	___fsmul
	mov	r4, dpl
	mov	r5, dph
	mov	r6, b
	mov	r7, a
	mov	a,sp
	add	a,#0xfc
	mov	sp,a
	mov	dpl, r4
	mov	dph, r5
	mov	b, r6
	mov	a, r7
;	./backend/backend/outputs/firmware_1746319894.c:106: }
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'init_uart'
;------------------------------------------------------------
;	./backend/backend/outputs/firmware_1746319894.c:112: void init_uart(void) {
;	-----------------------------------------
;	 function init_uart
;	-----------------------------------------
_init_uart:
;	./backend/backend/outputs/firmware_1746319894.c:113: SCON = 0x50;   // Mode 1 (8-bit UART), REN=1 (enable receiver)
	mov	_SCON,#0x50
;	./backend/backend/outputs/firmware_1746319894.c:114: TMOD &= 0x0F;  // Clear Timer 1 bits
	anl	_TMOD,#0x0f
;	./backend/backend/outputs/firmware_1746319894.c:115: TMOD |= 0x20;  // Timer 1 in Mode 2 (8-bit auto-reload)
	orl	_TMOD,#0x20
;	./backend/backend/outputs/firmware_1746319894.c:116: TH1 = 0xFD;    // Reload value for 9600 baud with 11.0592MHz crystal
	mov	_TH1,#0xfd
;	./backend/backend/outputs/firmware_1746319894.c:117: TR1 = 1;       // Start Timer 1
;	assignBit
	setb	_TR1
;	./backend/backend/outputs/firmware_1746319894.c:118: TI = 1;        // Set TI to indicate ready to transmit
;	assignBit
	setb	_TI
;	./backend/backend/outputs/firmware_1746319894.c:119: }
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'uart_tx_char'
;------------------------------------------------------------
;c             Allocated to registers 
;------------------------------------------------------------
;	./backend/backend/outputs/firmware_1746319894.c:124: void uart_tx_char(char c) {
;	-----------------------------------------
;	 function uart_tx_char
;	-----------------------------------------
_uart_tx_char:
	mov	_SBUF,dpl
;	./backend/backend/outputs/firmware_1746319894.c:126: while (!TI);   // Wait for transmission to complete
00101$:
;	./backend/backend/outputs/firmware_1746319894.c:127: TI = 0;        // Clear transmission flag
;	assignBit
	jbc	_TI,00118$
	sjmp	00101$
00118$:
;	./backend/backend/outputs/firmware_1746319894.c:128: }
	ret
;------------------------------------------------------------
;Allocation info for local variables in function 'uart_tx_string'
;------------------------------------------------------------
;str           Allocated to registers 
;------------------------------------------------------------
;	./backend/backend/outputs/firmware_1746319894.c:133: void uart_tx_string(char *str) {
;	-----------------------------------------
;	 function uart_tx_string
;	-----------------------------------------
_uart_tx_string:
	mov	r5, dpl
	mov	r6, dph
	mov	r7, b
;	./backend/backend/outputs/firmware_1746319894.c:134: while (*str) {
00101$:
	mov	dpl,r5
	mov	dph,r6
	mov	b,r7
	lcall	__gptrget
	mov	r4,a
	jz	00104$
;	./backend/backend/outputs/firmware_1746319894.c:135: uart_tx_char(*str++);
	mov	dpl,r4
	inc	r5
	cjne	r5,#0x00,00120$
	inc	r6
00120$:
	push	ar7
	push	ar6
	push	ar5
	lcall	_uart_tx_char
	pop	ar5
	pop	ar6
	pop	ar7
	sjmp	00101$
00104$:
;	./backend/backend/outputs/firmware_1746319894.c:137: }
	ret
	.area CSEG    (CODE)
	.area CONST   (CODE)
	.area CONST   (CODE)
___str_0:
	.ascii "System initialized"
	.db 0x0d
	.db 0x0a
	.db 0x00
	.area CSEG    (CODE)
	.area CONST   (CODE)
___str_1:
	.ascii "Temp: %.1f C"
	.db 0x0d
	.db 0x0a
	.db 0x00
	.area CSEG    (CODE)
	.area XINIT   (CODE)
	.area CABS    (ABS,CODE)
