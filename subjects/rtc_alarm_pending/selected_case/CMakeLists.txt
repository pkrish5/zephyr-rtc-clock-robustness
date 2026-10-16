cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(upstream_rtc_alarm_pending)

set(UPSTREAM_RTC_TEST ${CMAKE_CURRENT_LIST_DIR}/../../upstream/zephyr/tests/drivers/rtc/rtc_api/src)
target_sources(app PRIVATE
    ${UPSTREAM_RTC_TEST}/main.c
    ${UPSTREAM_RTC_TEST}/test_alarm.c)
target_compile_definitions(app PRIVATE CONFIG_TEST_RTC_ALARM_TIME_MASK=7)
