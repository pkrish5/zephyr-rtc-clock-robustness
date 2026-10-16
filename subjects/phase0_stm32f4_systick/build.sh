#!/bin/sh
set -eu
cd "$(dirname "$0")"
clang -target armv7em-none-eabi -mcpu=cortex-m4 -mthumb -O1 -ffreestanding -fno-builtin -nostdlib -c firmware.c -o firmware.o
clang -target armv7em-none-eabi -mcpu=cortex-m4 -mthumb -c startup.S -o startup.o
arm-none-eabi-ld -T linker.ld startup.o firmware.o -o firmware.elf
arm-none-eabi-objcopy -O binary firmware.elf firmware.bin
shasum -a 256 firmware.elf
