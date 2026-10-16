#!/usr/bin/env python3
"""Make an isolated STM32 RTC driver copy for descriptive quality challenges.

The pinned Zephyr driver is read only. The copy is linked in place of that
driver at CMake configure time. Neither variant belongs to the legal LSI arm.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "subjects/upstream/zephyr/drivers/rtc/rtc_ll_stm32.c"
DST = Path(__file__).with_name("rtc_ll_stm32_quality.c")


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError(f"Expected one source anchor, got {source.count(old)}: {old[:80]!r}")
    return source.replace(old, new)


source = SRC.read_text()
source = replace_once(source, '#include "rtc_ll_stm32.h"', '''#include "rtc_ll_stm32.h"

/* Isolated quality challenge. The production driver has no such macros. */
#ifndef QUALITY_DELAY_US
#define QUALITY_DELAY_US 0
#endif
#ifndef QUALITY_LATENCY_ALARM
#define QUALITY_LATENCY_ALARM 0
#endif
#ifndef QUALITY_LATENCY_COUNTING
#define QUALITY_LATENCY_COUNTING 0
#endif
#ifndef QUALITY_NONARRIVAL_ALARM
#define QUALITY_NONARRIVAL_ALARM 0
#endif
#ifndef QUALITY_NONARRIVAL_COUNTING
#define QUALITY_NONARRIVAL_COUNTING 0
#endif

#if QUALITY_LATENCY_COUNTING
static bool quality_first_read_pending;
#endif
#if QUALITY_NONARRIVAL_COUNTING
static bool quality_saved_set;
static struct rtc_time quality_saved_time;
#endif

static void quality_delay(const char *path)
{
    uint32_t before = k_cycle_get_32();
    if (QUALITY_DELAY_US > 0) {
        k_busy_wait(QUALITY_DELAY_US);
    }
    uint32_t cycles = k_cycle_get_32() - before;
    printk("QUALITY_DELAY path=%s request_us=%u cycles=%u hz=%u\\n",
           path, (unsigned int)QUALITY_DELAY_US, (unsigned int)cycles,
           (unsigned int)sys_clock_hw_cycles_per_sec());
}
''')
source = replace_once(source, '''\t\t\tp_rtc_alrm->is_pending = true;

\t\t\tif (p_rtc_alrm->user_callback != NULL) {
\t\t\t\tp_rtc_alrm->user_callback(dev, (uint16_t)id, p_rtc_alrm->user_data);
\t\t\t}
''', '''#if !QUALITY_NONARRIVAL_ALARM
#if QUALITY_LATENCY_ALARM
            quality_delay("alarm");
#endif
            p_rtc_alrm->is_pending = true;

            if (p_rtc_alrm->user_callback != NULL) {
                p_rtc_alrm->user_callback(dev, (uint16_t)id, p_rtc_alrm->user_data);
            }
#endif
''')
source = replace_once(source, '''\tk_spin_unlock(&data->lock, key);

\treturn err;
}

static int rtc_stm32_get_time''', '''\tk_spin_unlock(&data->lock, key);

#if QUALITY_LATENCY_COUNTING
    if (err == 0) {
        quality_first_read_pending = true;
    }
#endif
#if QUALITY_NONARRIVAL_COUNTING
    if (err == 0) {
        quality_saved_time = *timeptr;
        quality_saved_set = true;
    }
#endif
\treturn err;
}

static int rtc_stm32_get_time''')
source = replace_once(source, '''\tif (timeptr == NULL) {
\t\tLOG_ERR("NULL rtc_time pointer");
\t\treturn -EINVAL;
\t}

\tk_spinlock_key_t key = k_spin_lock(&data->lock);''', '''\tif (timeptr == NULL) {
\t\tLOG_ERR("NULL rtc_time pointer");
\t\treturn -EINVAL;
\t}

#if QUALITY_LATENCY_COUNTING
    if (quality_first_read_pending) {
        quality_first_read_pending = false;
        quality_delay("first_read");
    }
#endif
#if QUALITY_NONARRIVAL_COUNTING
    if (quality_saved_set) {
        *timeptr = quality_saved_time;
        return 0;
    }
#endif

\tk_spinlock_key_t key = k_spin_lock(&data->lock);''')
DST.write_text(source)
print(DST)
