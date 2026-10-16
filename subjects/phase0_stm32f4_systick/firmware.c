#include <stdint.h>

#define REG32(address) (*(volatile uint32_t *)(address))

#define RCC_AHB1ENR REG32(0x40023830u)
#define GPIOD_MODER REG32(0x40020C00u)
#define GPIOD_BSRR REG32(0x40020C18u)
#define SYST_CSR REG32(0xE000E010u)
#define SYST_RVR REG32(0xE000E014u)
#define SYST_CVR REG32(0xE000E018u)
#define SCB_VTOR REG32(0xE000ED08u)

volatile uint32_t irq_count;

void SysTick_Handler(void)
{
    irq_count++;
    GPIOD_BSRR = 1u << 12;
    SYST_CSR = 0;
}

void main(void)
{
    SCB_VTOR = 0x08000000u;
    irq_count = 0;

    RCC_AHB1ENR |= 1u << 3;
    GPIOD_MODER = (GPIOD_MODER & ~(3u << 24)) | (1u << 24);
    GPIOD_BSRR = 1u << 28;

    // One interrupt after 10 ms at the nominal 16 MHz HSI frequency.
    SYST_RVR = 160000u - 1u;
    SYST_CVR = 0;
    SYST_CSR = 0x7u;

    for (;;) {
        __asm__ volatile("wfi");
    }
}
