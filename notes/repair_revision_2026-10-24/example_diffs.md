# Approved V1 split: six updated diffs

Created before any repair compilation or run.

## V1: sol-range_absent-rtc_alarm_pending-r03

```diff
--- V0/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c
+++ V1/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c
@@ -5,6 +5,7 @@
 #include <zephyr/devicetree.h>
 #include <zephyr/drivers/rtc.h>
 #include <zephyr/kernel.h>
+#include <zephyr/sys/util.h>
 #include <zephyr/ztest.h>
 
 #define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
@@ -47,6 +48,7 @@
     int64_t deadline;
 
     zassert_true(device_is_ready(rtc));
+    const int64_t repair_deadline = k_uptime_get() + MAX(INT64_C(15000), INT64_C(20824));
     zassert_ok(rtc_set_time(rtc, &start));
     zassert_ok(rtc_alarm_set_time(rtc, 0, ALARM_MASK, &alarm));
     zassert_ok(rtc_alarm_get_time(rtc, 0, &mask, &readback));
@@ -55,8 +57,8 @@
     zassert_equal(readback.tm_min, alarm.tm_min);
     zassert_equal(readback.tm_sec, alarm.tm_sec);
 
-    /* The alarm is ten RTC seconds away; allow 15 wall-clock seconds. */
-    deadline = k_uptime_get() + 15000;
+    /* Share one 20,824-ms observation ceiling from the calendar reset. */
+    deadline = repair_deadline;
     while (k_uptime_get() < deadline) {
         zassert_ok(rtc_get_time(rtc, &now));
         if (!before_time(&now, &alarm)) {
@@ -75,20 +77,20 @@
             saw_after = pending > 0;
             break;
         }
-        k_sleep(K_MSEC(50));
+        k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(50), deadline - k_uptime_get()))));
     }
 
     zassert_true(saw_before, "no pre-alarm observation");
     zassert_true(reached, "RTC did not reach alarm time");
 
-    /* Allow three more seconds for the alarm status to become visible. */
+    /* Naive extension preserves the original separate service allowance. */
     deadline = k_uptime_get() + 3000;
     while (!saw_after && k_uptime_get() < deadline) {
         pending = rtc_alarm_is_pending(rtc, 0);
         zassert_true(pending >= 0);
         saw_after = pending > 0;
         if (!saw_after) {
-            k_sleep(K_MSEC(50));
+            k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(50), deadline - k_uptime_get()))));
         }
     }
     zassert_true(saw_after, "alarm never became pending");
```

## V1b: sol-range_absent-rtc_alarm_pending-r03

```diff
--- V0/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c
+++ V1b/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c
@@ -5,6 +5,7 @@
 #include <zephyr/devicetree.h>
 #include <zephyr/drivers/rtc.h>
 #include <zephyr/kernel.h>
+#include <zephyr/sys/util.h>
 #include <zephyr/ztest.h>
 
 #define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
@@ -47,6 +48,7 @@
     int64_t deadline;
 
     zassert_true(device_is_ready(rtc));
+    const int64_t repair_deadline = k_uptime_get() + 20824;
     zassert_ok(rtc_set_time(rtc, &start));
     zassert_ok(rtc_alarm_set_time(rtc, 0, ALARM_MASK, &alarm));
     zassert_ok(rtc_alarm_get_time(rtc, 0, &mask, &readback));
@@ -55,8 +57,8 @@
     zassert_equal(readback.tm_min, alarm.tm_min);
     zassert_equal(readback.tm_sec, alarm.tm_sec);
 
-    /* The alarm is ten RTC seconds away; allow 15 wall-clock seconds. */
-    deadline = k_uptime_get() + 15000;
+    /* Share one 20,824-ms observation ceiling from the calendar reset. */
+    deadline = repair_deadline;
     while (k_uptime_get() < deadline) {
         zassert_ok(rtc_get_time(rtc, &now));
         if (!before_time(&now, &alarm)) {
@@ -75,20 +77,20 @@
             saw_after = pending > 0;
             break;
         }
-        k_sleep(K_MSEC(50));
+        k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(50), deadline - k_uptime_get()))));
     }
 
     zassert_true(saw_before, "no pre-alarm observation");
     zassert_true(reached, "RTC did not reach alarm time");
 
-    /* Allow three more seconds for the alarm status to become visible. */
-    deadline = k_uptime_get() + 3000;
+    /* Preserve the service allowance, capped by the shared observation ceiling. */
+    deadline = MIN(k_uptime_get() + 3000, repair_deadline);
     while (!saw_after && k_uptime_get() < deadline) {
         pending = rtc_alarm_is_pending(rtc, 0);
         zassert_true(pending >= 0);
         saw_after = pending > 0;
         if (!saw_after) {
-            k_sleep(K_MSEC(50));
+            k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(50), deadline - k_uptime_get()))));
         }
     }
     zassert_true(saw_after, "alarm never became pending");
```

## V1: sol-range_absent-rtc_time_counting-r01

**No source changes:** the original 60-second wait is retained.

## V1b: sol-range_absent-rtc_time_counting-r01

```diff
--- V0/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_time_counting/r01/test.c
+++ V1b/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_time_counting/r01/test.c
@@ -3,6 +3,9 @@
 #include <zephyr/drivers/rtc.h>
 #include <zephyr/kernel.h>
 #include <zephyr/ztest.h>
+
+#define REPAIR_EVENT_WAIT 0
+#include "repair_wait.h"
 
 /* Seconds since 2023-12-31 23:59:55, for dates this test can observe. */
 static int seconds_from_start(const struct rtc_time *t)
@@ -42,7 +45,7 @@
 		     "initial calendar does not match the set time");
 
 	/* Allow 60 wall-clock seconds for ten independent LSI-driven RTC ticks. */
-	for (int i = 0; i < 600 && previous < 10; i++) {
+	for (int i = 0; !repair_expired() && previous < 10; i++) {
 		int current;
 
 		k_sleep(K_MSEC(100));
```

The added `repair_wait.h` anchors the deadline at calendar reset and clamps each sleep.

## V1: human-rtc_alarm_callback

```diff
--- V0/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c
+++ V1/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c
@@ -9,6 +9,9 @@
 #include <zephyr/device.h>
 #include <zephyr/drivers/rtc.h>
 #include <zephyr/sys/atomic.h>
+#include <zephyr/kernel.h>
+#include <zephyr/sys/util.h>
+#include <stdint.h>
 
 #define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY (3)
 #define RTC_TEST_ALARM_TEST_CALLED_DELAY     (10)
@@ -68,6 +71,7 @@
 	atomic_val_t callback_called_mask_status_odd;
 	atomic_val_t callback_called_mask_status_even;
 	bool callback_called_status;
+	int64_t repair_deadline;
 
 	/* Disable alarm callback */
 	for (uint16_t i = 0; i < alarms_count; i++) {
@@ -87,6 +91,7 @@
 	}
 
 	/* Set RTC time */
+	repair_deadline = k_uptime_get() + MAX(INT64_C(13000), INT64_C(20824));
 	ret = rtc_set_time(rtc, &test_rtc_time_set);
 	zassert_ok(ret, "Failed to set time");
 
@@ -129,7 +134,7 @@
 			      "Alarm callback called prematurely");
 
 		/* Wait for alarm to trigger */
-		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_CALLED_DELAY));
+		k_sleep(K_MSEC(MAX(INT64_C(0), repair_deadline - k_uptime_get())));
 
 		/* Validate alarm callback called */
 		for (uint16_t j = 0; j < alarms_count; j++) {
@@ -142,6 +147,7 @@
 		}
 
 		/* Reset RTC time */
+		repair_deadline = k_uptime_get() + MAX(INT64_C(13000), INT64_C(20824));
 		ret = rtc_set_time(rtc, &test_rtc_time_set);
 		zassert_ok(ret, "Failed to set time");
 	}
```

## V1b: human-rtc_alarm_callback

```diff
--- V0/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c
+++ V1b/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c
@@ -9,6 +9,9 @@
 #include <zephyr/device.h>
 #include <zephyr/drivers/rtc.h>
 #include <zephyr/sys/atomic.h>
+#include <zephyr/kernel.h>
+#include <zephyr/sys/util.h>
+#include <stdint.h>
 
 #define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY (3)
 #define RTC_TEST_ALARM_TEST_CALLED_DELAY     (10)
@@ -68,6 +71,7 @@
 	atomic_val_t callback_called_mask_status_odd;
 	atomic_val_t callback_called_mask_status_even;
 	bool callback_called_status;
+	int64_t repair_deadline;
 
 	/* Disable alarm callback */
 	for (uint16_t i = 0; i < alarms_count; i++) {
@@ -87,6 +91,7 @@
 	}
 
 	/* Set RTC time */
+	repair_deadline = k_uptime_get() + 20824;
 	ret = rtc_set_time(rtc, &test_rtc_time_set);
 	zassert_ok(ret, "Failed to set time");
 
@@ -129,7 +134,7 @@
 			      "Alarm callback called prematurely");
 
 		/* Wait for alarm to trigger */
-		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_CALLED_DELAY));
+		k_sleep(K_MSEC(MAX(INT64_C(0), repair_deadline - k_uptime_get())));
 
 		/* Validate alarm callback called */
 		for (uint16_t j = 0; j < alarms_count; j++) {
@@ -142,6 +147,7 @@
 		}
 
 		/* Reset RTC time */
+		repair_deadline = k_uptime_get() + 20824;
 		ret = rtc_set_time(rtc, &test_rtc_time_set);
 		zassert_ok(ret, "Failed to set time");
 	}
```

## Added counting wait adapter (V1b)

```c
/* Registered mechanical waiting adapter; original assertions remain below.
 * Original timeout messages may still describe V0's budget.
 */
#ifndef REPAIR_WAIT_H
#define REPAIR_WAIT_H
#include <zephyr/kernel.h>
#include <zephyr/drivers/rtc.h>
#include <zephyr/sys/util.h>
#include <stdint.h>
#include <stdbool.h>
static int64_t repair_deadline;
static int repair_set_time(const struct device *dev, const struct rtc_time *value)
{
    repair_deadline = k_uptime_get() + 20824;
    return rtc_set_time(dev, value);
}
static inline bool repair_expired(void)
{
    return k_uptime_get() >= repair_deadline;
}
static int32_t repair_sleep(k_timeout_t requested)
{
    int64_t wait_ms = k_ticks_to_ms_ceil64(requested.ticks);
    int64_t remaining = MAX(INT64_C(0), repair_deadline - k_uptime_get());
    if (REPAIR_EVENT_WAIT) {
        wait_ms = MIN(wait_ms, INT64_C(20));
    }
    return k_sleep(K_MSEC(MIN(wait_ms, remaining)));
}
static inline void repair_fixed_wait(void)
{
    k_sleep(K_MSEC(MAX(INT64_C(0), repair_deadline - k_uptime_get())));
}
#define rtc_set_time repair_set_time
#define k_sleep repair_sleep
#define k_msleep(ms) repair_sleep(K_MSEC(ms))
#endif
```
