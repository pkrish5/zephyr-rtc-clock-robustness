# E repair examples for approval

No variants were built or run. Each diff is against the frozen V0 source.

## V1: upstream_callback

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

## V2: upstream_callback

```diff
--- V0/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c
+++ V2/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c
@@ -9,6 +9,9 @@
 #include <zephyr/device.h>
 #include <zephyr/drivers/rtc.h>
 #include <zephyr/sys/atomic.h>
+#include <zephyr/kernel.h>
+#include <zephyr/sys/util.h>
+#include <stdint.h>
 
 #define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY (3)
 #define RTC_TEST_ALARM_TEST_CALLED_DELAY     (10)
@@ -62,12 +65,25 @@
 	atomic_set_bit(&callback_called_mask_even, id);
 }
 
+static bool repair_all_called(void)
+{
+	for (uint16_t id = 0; id < alarms_count; ++id) {
+		bool called = (id % 2) ? atomic_test_bit(&callback_called_mask_odd, id)
+				       : atomic_test_bit(&callback_called_mask_even, id);
+		if (!called) {
+			return false;
+		}
+	}
+	return true;
+}
+
 ZTEST(rtc_api, test_alarm_callback)
 {
 	int ret;
 	atomic_val_t callback_called_mask_status_odd;
 	atomic_val_t callback_called_mask_status_even;
 	bool callback_called_status;
+	int64_t repair_deadline;
 
 	/* Disable alarm callback */
 	for (uint16_t i = 0; i < alarms_count; i++) {
@@ -87,6 +103,7 @@
 	}
 
 	/* Set RTC time */
+	repair_deadline = k_uptime_get() + 20824;
 	ret = rtc_set_time(rtc, &test_rtc_time_set);
 	zassert_ok(ret, "Failed to set time");
 
@@ -129,7 +146,13 @@
 			      "Alarm callback called prematurely");
 
 		/* Wait for alarm to trigger */
-		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_CALLED_DELAY));
+		while (!repair_all_called() && k_uptime_get() < repair_deadline) {
+			int64_t repair_remaining = repair_deadline - k_uptime_get();
+			if (repair_remaining <= 0) {
+				break;
+			}
+			k_sleep(K_MSEC(MIN(INT64_C(20), repair_remaining)));
+		}
 
 		/* Validate alarm callback called */
 		for (uint16_t j = 0; j < alarms_count; j++) {
@@ -142,6 +165,7 @@
 		}
 
 		/* Reset RTC time */
+		repair_deadline = k_uptime_get() + 20824;
 		ret = rtc_set_time(rtc, &test_rtc_time_set);
 		zassert_ok(ret, "Failed to set time");
 	}
```

## V3: upstream_callback

```diff
--- V0/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c
+++ V3/subjects/upstream/zephyr/tests/drivers/rtc/rtc_api/src/test_alarm_callback.c
@@ -9,6 +9,9 @@
 #include <zephyr/device.h>
 #include <zephyr/drivers/rtc.h>
 #include <zephyr/sys/atomic.h>
+#include <zephyr/kernel.h>
+#include <zephyr/sys/util.h>
+#include <stdint.h>
 
 #define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY (3)
 #define RTC_TEST_ALARM_TEST_CALLED_DELAY     (10)
@@ -50,16 +53,60 @@
 	.tm_nsec = 0,
 };
 
+static struct rtc_time repair_callback_time[DT_PROP(DT_ALIAS(rtc), alarms_count)];
+static int repair_callback_read_rc[DT_PROP(DT_ALIAS(rtc), alarms_count)];
+static atomic_t repair_bad_id;
+
+static bool repair_capture(const struct device *dev, uint16_t id, uint16_t parity)
+{
+	if (dev != rtc || id >= alarms_count || (id % 2) != parity) {
+		atomic_set(&repair_bad_id, 1);
+		return false;
+	}
+	repair_callback_read_rc[id] = rtc_get_time(dev, &repair_callback_time[id]);
+	return true;
+}
+
+static int repair_calendar_cmp(const struct rtc_time *a, const struct rtc_time *b)
+{
+	const int av[] = {a->tm_year, a->tm_mon, a->tm_mday, a->tm_hour, a->tm_min, a->tm_sec};
+	const int bv[] = {b->tm_year, b->tm_mon, b->tm_mday, b->tm_hour, b->tm_min, b->tm_sec};
+	for (size_t i = 0; i < ARRAY_SIZE(av); ++i) {
+		if (av[i] != bv[i]) {
+			return (av[i] < bv[i]) ? -1 : 1;
+		}
+	}
+	return 0;
+}
+
 static void test_rtc_alarm_callback_handler_odd(const struct device *dev, uint16_t id,
 						void *user_data)
 {
+	if (!repair_capture(dev, id, 1)) {
+		return;
+	}
 	atomic_set_bit(&callback_called_mask_odd, id);
 }
 
 static void test_rtc_alarm_callback_handler_even(const struct device *dev, uint16_t id,
 						 void *user_data)
 {
+	if (!repair_capture(dev, id, 0)) {
+		return;
+	}
 	atomic_set_bit(&callback_called_mask_even, id);
+}
+
+static bool repair_all_called(void)
+{
+	for (uint16_t id = 0; id < alarms_count; ++id) {
+		bool called = (id % 2) ? atomic_test_bit(&callback_called_mask_odd, id)
+				       : atomic_test_bit(&callback_called_mask_even, id);
+		if (!called) {
+			return false;
+		}
+	}
+	return true;
 }
 
 ZTEST(rtc_api, test_alarm_callback)
@@ -68,6 +115,9 @@
 	atomic_val_t callback_called_mask_status_odd;
 	atomic_val_t callback_called_mask_status_even;
 	bool callback_called_status;
+	int64_t repair_deadline;
+	struct rtc_time repair_alarm_readback;
+	uint16_t repair_alarm_mask;
 
 	/* Disable alarm callback */
 	for (uint16_t i = 0; i < alarms_count; i++) {
@@ -84,9 +134,15 @@
 	for (uint16_t i = 0; i < alarms_count; i++) {
 		ret = rtc_alarm_set_time(rtc, i, test_alarm_time_mask_set, &test_alarm_time_set);
 		zassert_ok(ret, "Failed to set alarm %d time", i);
+		zassert_ok(rtc_alarm_get_time(rtc, i, &repair_alarm_mask, &repair_alarm_readback));
+		zassert_equal(repair_alarm_mask, test_alarm_time_mask_set);
+		zassert_equal(repair_alarm_readback.tm_hour, test_alarm_time_set.tm_hour);
+		zassert_equal(repair_alarm_readback.tm_min, test_alarm_time_set.tm_min);
+		zassert_equal(repair_alarm_readback.tm_sec, test_alarm_time_set.tm_sec);
 	}
 
 	/* Set RTC time */
+	repair_deadline = k_uptime_get() + 20824;
 	ret = rtc_set_time(rtc, &test_rtc_time_set);
 	zassert_ok(ret, "Failed to set time");
 
@@ -112,6 +168,10 @@
 	}
 
 	for (uint8_t i = 0; i < 2; i++) {
+		atomic_set(&repair_bad_id, 0);
+		for (uint16_t id = 0; id < alarms_count; ++id) {
+			repair_callback_read_rc[id] = -EAGAIN;
+		}
 		/* Clear callback called atomics */
 		atomic_set(&callback_called_mask_odd, 0);
 		atomic_set(&callback_called_mask_even, 0);
@@ -129,8 +189,15 @@
 			      "Alarm callback called prematurely");
 
 		/* Wait for alarm to trigger */
-		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_CALLED_DELAY));
-
+		while (!repair_all_called() && k_uptime_get() < repair_deadline) {
+			int64_t repair_remaining = repair_deadline - k_uptime_get();
+			if (repair_remaining <= 0) {
+				break;
+			}
+			k_sleep(K_MSEC(MIN(INT64_C(20), repair_remaining)));
+		}
+
+		zassert_equal(atomic_get(&repair_bad_id), 0, "Unexpected callback device/ID");
 		/* Validate alarm callback called */
 		for (uint16_t j = 0; j < alarms_count; j++) {
 			callback_called_status =
@@ -139,9 +206,15 @@
 
 			zassert_equal(callback_called_status, true,
 				      "Alarm %d callback should have been called", j);
+			zassert_ok(repair_callback_read_rc[j], "Failed to capture callback RTC calendar");
+			zassert_true(repair_calendar_cmp(&repair_callback_time[j], &test_alarm_time_set) >= 0,
+				     "Callback before target calendar");
+			zassert_equal(repair_calendar_cmp(&repair_callback_time[j], &test_alarm_time_set), 0,
+				      "Callback outside target RTC second");
 		}
 
 		/* Reset RTC time */
+		repair_deadline = k_uptime_get() + 20824;
 		ret = rtc_set_time(rtc, &test_rtc_time_set);
 		zassert_ok(ret, "Failed to set time");
 	}
```

## V1: generated_sol_pending

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

## V2: generated_sol_pending

```diff
--- V0/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c
+++ V2/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c
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
+        k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(20), deadline - k_uptime_get()))));
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
+            k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(20), deadline - k_uptime_get()))));
         }
     }
     zassert_true(saw_after, "alarm never became pending");
```

## V3: generated_sol_pending

```diff
--- V0/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c
+++ V3/generated/spec_context_factorial_v1/suites/sol/range_absent/rtc_alarm_pending/r03/test.c
@@ -5,6 +5,7 @@
 #include <zephyr/devicetree.h>
 #include <zephyr/drivers/rtc.h>
 #include <zephyr/kernel.h>
+#include <zephyr/sys/util.h>
 #include <zephyr/ztest.h>
 
 #define ALARM_MASK (RTC_ALARM_TIME_MASK_SECOND | \
@@ -39,6 +40,8 @@
     };
     struct rtc_time readback;
     struct rtc_time now;
+    struct rtc_time repair_pending_before;
+    struct rtc_time repair_pending_after;
     uint16_t mask = 0;
     bool saw_before = false;
     bool saw_after = false;
@@ -47,6 +50,7 @@
     int64_t deadline;
 
     zassert_true(device_is_ready(rtc));
+    const int64_t repair_deadline = k_uptime_get() + 20824;
     zassert_ok(rtc_set_time(rtc, &start));
     zassert_ok(rtc_alarm_set_time(rtc, 0, ALARM_MASK, &alarm));
     zassert_ok(rtc_alarm_get_time(rtc, 0, &mask, &readback));
@@ -55,8 +59,8 @@
     zassert_equal(readback.tm_min, alarm.tm_min);
     zassert_equal(readback.tm_sec, alarm.tm_sec);
 
-    /* The alarm is ten RTC seconds away; allow 15 wall-clock seconds. */
-    deadline = k_uptime_get() + 15000;
+    /* Share one 20,824-ms observation ceiling from the calendar reset. */
+    deadline = repair_deadline;
     while (k_uptime_get() < deadline) {
         zassert_ok(rtc_get_time(rtc, &now));
         if (!before_time(&now, &alarm)) {
@@ -75,20 +79,26 @@
             saw_after = pending > 0;
             break;
         }
-        k_sleep(K_MSEC(50));
+        k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(20), deadline - k_uptime_get()))));
     }
 
     zassert_true(saw_before, "no pre-alarm observation");
     zassert_true(reached, "RTC did not reach alarm time");
 
-    /* Allow three more seconds for the alarm status to become visible. */
-    deadline = k_uptime_get() + 3000;
+    /* Preserve the service allowance, capped by the shared observation ceiling. */
+    deadline = MIN(k_uptime_get() + 3000, repair_deadline);
     while (!saw_after && k_uptime_get() < deadline) {
+        zassert_ok(rtc_get_time(rtc, &repair_pending_before));
         pending = rtc_alarm_is_pending(rtc, 0);
         zassert_true(pending >= 0);
+        zassert_ok(rtc_get_time(rtc, &repair_pending_after));
+        if (pending > 0) {
+            zassert_false(before_time(&repair_pending_after, &alarm),
+                          "pending observed before configured calendar target");
+        }
         saw_after = pending > 0;
         if (!saw_after) {
-            k_sleep(K_MSEC(50));
+            k_sleep(K_MSEC(MAX(INT64_C(0), MIN(INT64_C(20), deadline - k_uptime_get()))));
         }
     }
     zassert_true(saw_after, "alarm never became pending");
```

