cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(reference_rtc_counting)
target_sources(app PRIVATE test.c)
