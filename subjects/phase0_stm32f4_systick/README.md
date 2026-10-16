# Phase 0 STM32F4 SysTick fixture

This deliberately small firmware targets the STM32F407VG model used by Renode's STM32F4 Discovery platform. It configures GPIOD pin 12 as an output, programs SysTick for 160,000 processor clocks, waits for the interrupt, and raises the pin in the ISR. The test oracle reads the GPIO output data register at `0x40020C14`.

Build with `sh build.sh` after installing Apple Clang with Arm cross-target support and `arm-none-eabi-binutils`. The resulting ELF is the firmware artifact frozen across nominal and perturbed runs. `firmware.c` and `startup.S` are project-authored Phase 0 fixtures, not a Zephyr sample or an agent output.

At reset the STM32F407 CPU uses the 16 MHz HSI clock ([STM32F407 datasheet](https://www.st.com/resource/en/datasheet/stm32f407ig.pdf)). `SYST_CSR=0x7` enables SysTick, its interrupt, and the processor-clock source ([STM32 Cortex-M4 programming manual](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf)). The simulator platform is generated from Renode's packaged STM32F4 description with its `systickFrequency` parameter set to the sampled HSI value. This fixture is a mechanism check; no physical board has been tested.
