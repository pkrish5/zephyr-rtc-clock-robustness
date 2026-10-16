.syntax unified
.cpu cortex-m4
.thumb

.section .vectors, "a", %progbits
.global vector_table
vector_table:
    .word 0x20010000
    .word Reset_Handler
    .rept 13
    .word Default_Handler
    .endr
    .word SysTick_Handler

.section .text.Reset_Handler, "ax", %progbits
.thumb_func
.global Reset_Handler
Reset_Handler:
    ldr sp, =0x20010000
    bl main
1:  b 1b

.section .text.Default_Handler, "ax", %progbits
.thumb_func
.global Default_Handler
Default_Handler:
2:  b 2b
