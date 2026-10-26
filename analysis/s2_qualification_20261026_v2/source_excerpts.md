# Qualification failure source excerpts

Source hashes match the sealed S2 upstream-input ledger. These are preliminary
explanations, not completed production attribution. Phase-dependent expressions
assume divider 32000; phi is the fractional tick at alarm programming.

## rtc_api.test_alarm

`tests/drivers/rtc/rtc_api/src/test_alarm.c`

```c
14: #define RTC_TEST_ALARM_TEST_NOT_PENDING_DELAY (3)
15: #define RTC_TEST_ALARM_TEST_PENDING_DELAY     (10)

177: 	for (uint8_t k = 0; k < 2; k++) {
178: 		/* Set RTC time */
179: 		ret = rtc_set_time(rtc, &test_rtc_time_set);
180: 		zassert_ok(ret, "Failed to set time");
181: 
182: 		/* Clear alarm pending status */
183: 		for (uint16_t i = 0; i < alarms_count; i++) {
184: 			ret = rtc_alarm_is_pending(rtc, i);
185: 			zassert_true(ret > -1, "Failed to clear alarm %d pending status", i);
186: 		}
187: 
188: 		/* Wait before validating alarm pending status has not been set prematurely */
189: 		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_NOT_PENDING_DELAY));
190: 
191: 		/* Validate alarm are not pending */
192: 		for (uint16_t i = 0; i < alarms_count; i++) {
193: 			ret = rtc_alarm_is_pending(rtc, i);
194: 			zassert_ok(ret, "Alarm %d should not be pending", i);
195: 		}
196: 
197: 		/* Wait for alarm to trigger */
198: 		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_PENDING_DELAY));
199: 
200: 		/* Validate alarm is pending */
201: 		for (uint16_t i = 0; i < alarms_count; i++) {
202: 			ret = rtc_alarm_is_pending(rtc, i);
203: 			zassert_equal(ret, 1, "Alarm %d should be pending", i);
204: 		}

```

## rtc_api.test_alarm_callback

`tests/drivers/rtc/rtc_api/src/test_alarm_callback.c`

```c
13: #define RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY (3)
14: #define RTC_TEST_ALARM_TEST_CALLED_DELAY     (10)

119: 		/* Wait before validating alarm callbacks have not been called prematurely */
120: 		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_NOT_CALLED_DELAY));
121: 
122: 		/* Validate alarm callbacks have not been called prematurely */
123: 		callback_called_mask_status_odd = atomic_get(&callback_called_mask_odd);
124: 		callback_called_mask_status_even = atomic_get(&callback_called_mask_even);
125: 
126: 		zassert_equal(callback_called_mask_status_odd, 0,
127: 			      "Alarm callback called prematurely");
128: 		zassert_equal(callback_called_mask_status_even, 0,
129: 			      "Alarm callback called prematurely");
130: 
131: 		/* Wait for alarm to trigger */
132: 		k_sleep(K_SECONDS(RTC_TEST_ALARM_TEST_CALLED_DELAY));
133: 
134: 		/* Validate alarm callback called */
135: 		for (uint16_t j = 0; j < alarms_count; j++) {
136: 			callback_called_status =
137: 				(j % 2) ? atomic_test_bit(&callback_called_mask_odd, j)
138: 					: atomic_test_bit(&callback_called_mask_even, j);
139: 
140: 			zassert_equal(callback_called_status, true,
141: 				      "Alarm %d callback should have been called", j);

```

## rtc_api.test_time_counting

`tests/drivers/rtc/rtc_api/src/test_time_incrementing.c`

```c
15: #define RTC_TEST_TIME_COUNTING_SET_TIME	  (1767225595UL)
16: #define RTC_TEST_TIME_COUNTING_LIMIT	  (RTC_TEST_TIME_COUNTING_SET_TIME + 10UL)
17: #define RTC_TEST_TIME_COUNTING_POLL_LIMIT (30U)

35: 	zassert_equal(rtc_set_time(rtc, &datetime_set), 0, "Failed to set time");
36: 
37: 	for (i = 0; i < RTC_TEST_TIME_COUNTING_POLL_LIMIT; i++) {
38: 		/* Get time */
39: 		zassert_equal(rtc_get_time(rtc, &datetime_get), 0, "Failed to get time");
40: 
41: 		timer_get = timeutil_timegm((struct tm *)(&datetime_get));
42: 
43: 		/* Validate if time incrementing */
44: 		zassert_true(timer_get_last <= timer_get, "Time is decrementing");
45: 
46: 		/* Check if limit reached */
47: 		if (timer_get == RTC_TEST_TIME_COUNTING_LIMIT) {
48: 			break;
49: 		}
50: 
51: 		/* Save last timer get */
52: 		timer_get_last = timer_get;
53: 
54: 		/* Limit polling rate */
55: 		k_msleep(500);
56: 	}
57: 
58: 	zassert_true(i < RTC_TEST_TIME_COUNTING_POLL_LIMIT,
59: 		     "Timeout occurred waiting for time to increment");

```

## counter_basic.test_all_channels

`tests/drivers/counter/counter_basic_api/src/test_counter.c`

```c
179: static inline uint32_t get_counter_period_us(const struct device *dev)
180: {
181: 	for (int i = 0; i < ARRAY_SIZE(period_devs); i++) {
182: 		if (period_devs[i] == dev) {
183: 			return (USEC_PER_SEC * 2U);
184: 		}
185: 	}

658: static void test_all_channels_instance(const struct device *dev)
659: {
660: 	int err;
661: 	const int n = 10;
662: 	int nchan = 0;
663: 	bool limit_reached = false;
664: 	struct counter_alarm_cfg alarm_cfgs;
665: 	uint32_t ticks;
666: 	uint32_t cnt;
667: 	uint32_t counter_period_us;
668: 
669: 	counter_period_us = get_counter_period_us(dev);
670: 	ticks = counter_us_to_ticks(dev, counter_period_us);
671: 
672: 	alarm_cfgs.flags = 0;
673: 	alarm_cfgs.ticks = ticks;
674: 	alarm_cfgs.callback = alarm_handler2;
675: 	alarm_cfgs.user_data = NULL;
676: 
677: 	err = counter_start(dev);
678: 	zassert_equal(0, err, "%s: Counter failed to start", dev->name);
679: 
680: 	for (int i = 0; i < n; i++) {
681: 		err = counter_set_channel_alarm(dev, i, &alarm_cfgs);
682: 		if ((err == 0) && !limit_reached) {
683: 			nchan++;
684: 		} else if (err == -ENOTSUP) {
685: 			limit_reached = true;
686: 		} else {
687: 			zassert_equal(0, 1,
688: 			   "%s: Unexpected error on setting alarm", dev->name);
689: 		}
690: 	}
691: 
692: 	k_busy_wait(1.5*counter_ticks_to_us(dev, ticks));
693: 	cnt = IS_ENABLED(CONFIG_ZERO_LATENCY_IRQS) ?
694: 		alarm_cnt : k_sem_count_get(&alarm_cnt_sem);
695: 	zassert_equal(nchan, cnt,
696: 			"%s: Expecting alarm callback", dev->name);
697: 
698: 	for (int i = 0; i < nchan; i++) {
699: 		err = counter_cancel_channel_alarm(dev, i);
700: 		zassert_equal(0, err,
701: 			"%s: Unexpected error on disabling alarm", dev->name);
702: 	}

```

## counter_basic.test_single_shot_alarm_notop

`tests/drivers/counter/counter_basic_api/src/test_counter.c`

```c
473: 	cntr_alarm_cfg.ticks = ticks;
474: 	err = counter_set_channel_alarm(dev, 0, &cntr_alarm_cfg);
475: 	zassert_equal(0, err, "%s: Counter set alarm failed (err: %d)",
476: 			dev->name, err);
477: 
478: 	k_busy_wait(2*(uint32_t)counter_ticks_to_us(dev, ticks));

```

## seconds_counter.test_seconds_rate

`tests/drivers/counter/counter_seconds/src/main.c`

```c
20: #define DELAY_MS 1200	/* pause 1.2 seconds should always pass */
21: #define MIN_BOUND 1	/* counter must report at least MIN_BOUND .. */
22: #define MAX_BOUND 2	/* .. but at most MAX_BOUND seconds elapsed */
23: 
24: ZTEST(seconds_counter, test_seconds_rate)
25: {
26: 	const struct device *const dev = DEVICE_DT_GET(CTR_DEV);
27: 	uint32_t start, elapsed;
28: 	int err;
29: 
30: 	zassert_true(device_is_ready(dev), "counter device is not ready");
31: 
32: 	err = counter_get_value(dev, &start);
33: 	zassert_true(err == 0, "failed to read counter device");
34: 
35: 	k_msleep(DELAY_MS);
36: 
37: 	err = counter_get_value(dev, &elapsed);
38: 	zassert_true(err == 0, "failed to read counter device");
39: 	elapsed -= start;
40: 
41: 	zassert_true(elapsed >= MIN_BOUND, "busted minimum bound");
42: 	zassert_true(elapsed <= MAX_BOUND, "busted maximum bound");

```

## Driver relative-alarm offset and busy guard

`drivers/counter/counter_ll_stm32_rtc.c`

```c
517: 	tick_t now = rtc_stm32_read(dev);
518: 	tick_t ticks = alarm_cfg->ticks;
519: 
520: 	if (data->callback != NULL) {
521: 		LOG_DBG("Alarm busy");
522: 		return -EBUSY;
523: 	}
524: 
525: 
526: 	data->callback = alarm_cfg->callback;
527: 	data->user_data = alarm_cfg->user_data;
528: 
529: #if !defined(COUNTER_NO_DATE)
530: 	if ((alarm_cfg->flags & COUNTER_ALARM_CFG_ABSOLUTE) == 0) {
531: 		/* Add +1 in order to compensate the partially started tick.
532: 		 * Alarm will expire between requested ticks and ticks+1.
533: 		 * In case only 1 tick is requested, it will avoid
534: 		 * that tick+1 event occurs before alarm setting is finished.
535: 		 */
536: 		ticks += now + 1;
537: 		alarm_val_s = (time_t)(ticks / counter_get_frequency(dev)) + T_TIME_OFFSET;
```
