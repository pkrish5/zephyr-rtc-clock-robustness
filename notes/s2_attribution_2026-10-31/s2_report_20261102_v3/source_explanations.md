# S2 source explanations, 2026-11-02

Post-result source review; reference validation is not complete.

## rtc_api.test_alarm

First case in the application; the final alarm-pending assertion requires ten calendar seconds within thirteen host seconds. Its observed vector agrees with the isolated-case vector. The second source repetition is bypassed when the first assertion fails.

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

The calendar write changes date/time but the Renode model retains the fractional ticker count. Prior cases therefore change the remaining ten-second calendar delay. The thirteen-second observation can expire before callback delivery. Phase is inferred from source and boundary shifts, not directly measured.

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

The calendar-write model preserves the tick phase left by preceding cases. The final calendar observation occurs before the final sleep and timeout assertion; the assertion duration is not the observation budget. The full-application boundary moves below the isolated-case boundary.

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

The RTC counter driver adds one tick to a relative alarm to compensate the partially started tick. Delivery can require two to three physical ticks, whereas the test waits three host seconds calculated from nominal reported frequency. This phase subtype is a free-running counter phase, not a calendar-write claim.

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

The earlier all-channels assertion bypasses alarm cancellation and teardown. This later case fails alarm setup with -16 (-EBUSY), and the driver rejects setup while a callback remains registered. It fails at exactly the earlier case settings. Retain the primary failure, but do not count another independent waiting defect; causality remains source-supported without isolation/reference intervention.

`tests/drivers/counter/counter_basic_api/src/test_counter.c`

```c
225: 
226: static void test_all_instances(counter_test_func_t func,
227: 				counter_capability_func_t capability_check)
228: {
229: 	int devices_skipped = 0;
230: 
231: 	zassert_true(ARRAY_SIZE(devices) > 0, "No device found");
232: 	for (int i = 0; i < ARRAY_SIZE(devices); i++) {
233: 		counter_setup_instance(devices[i]);
234: 		if ((capability_check == NULL) ||
235: 		     capability_check(devices[i])) {
236: 			TC_PRINT("Testing %s\n", devices[i]->name);
237: 			func(devices[i]);
238: 		} else {
239: 			TC_PRINT("Skipped for %s\n", devices[i]->name);
240: 			devices_skipped++;
241: 		}
242: 		counter_tear_down_instance(devices[i]);
243: 		/* Allow logs to be printed. */
244: 		k_sleep(K_MSEC(100));
245: 	}
246: 	if (devices_skipped == ARRAY_SIZE(devices)) {
247: 		ztest_test_skip();
248: 	}
249: }
473: 	cntr_alarm_cfg.ticks = ticks;
474: 	err = counter_set_channel_alarm(dev, 0, &cntr_alarm_cfg);
475: 	zassert_equal(0, err, "%s: Counter set alarm failed (err: %d)",
476: 			dev->name, err);
477: 
478: 	k_busy_wait(2*(uint32_t)counter_ticks_to_us(dev, ticks));
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
```

## seconds_counter.test_seconds_rate

The case explicitly checks roughly 1 Hz and fails its minimum progress assertion. Its observed transition brackets the ideal 32000/1.2 comparison, but a legal-input sensitivity is not necessarily a spurious test failure. The intended clock-accuracy contract has not been established; a relaxed eventual-progress reference would not settle it.

`tests/drivers/counter/counter_seconds/src/main.c`

```c
10: /*
11:  * Basic test to ensure that the clock is ticking at roughly 1Hz.
12:  */
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

## drivers/counter/counter_ll_stm32_rtc.c

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
689: 	counter_alarm_callback_t alarm_callback = data->callback;
690: 
691: 	uint32_t now = rtc_stm32_read(dev);
692: 
693: 	if (ll_func_is_active_alarm(RTC) != 0
694: #ifdef CONFIG_COUNTER_RTC_STM32_SUBSECONDS
695: 	    || (data->irq_on_late && ll_func_isenabled_interrupt_alarm(RTC))
696: #endif /* CONFIG_COUNTER_RTC_STM32_SUBSECONDS */
697: 	) {
698: 
699: 		stm32_backup_domain_enable_access();
700: 		LL_RTC_DisableWriteProtection(RTC);
701: 		ll_func_clear_alarm_flag(RTC);
702: 		ll_func_disable_interrupt_alarm(RTC);
703: 		ll_func_disable_alarm(RTC);
704: 		LL_RTC_EnableWriteProtection(RTC);
705: 		stm32_backup_domain_disable_access();
706: #ifdef CONFIG_COUNTER_RTC_STM32_SUBSECONDS
707: 		data->irq_on_late = 0;
708: #endif /* CONFIG_COUNTER_RTC_STM32_SUBSECONDS */
709: 
710: 		if (alarm_callback != NULL) {
711: 			data->callback = NULL;
712: 			alarm_callback(dev, 0, now, data->user_data);
713: 		}
```

## drivers/rtc/rtc_ll_stm32.c

```c
536: static int rtc_stm32_set_time(const struct device *dev, const struct rtc_time *timeptr)
537: {
538: 	struct rtc_stm32_data *data = dev->data;
539: 	uint32_t real_year = timeptr->tm_year + TM_YEAR_REF;
540: 	int err;
541: 
542: 	if (real_year < RTC_YEAR_REF) {
543: 		/* RTC does not support years before 2000 */
544: 		return -EINVAL;
545: 	}
546: 
547: 	if (timeptr->tm_wday == -1) {
548: 		/* day of the week is expected */
549: 		return -EINVAL;
550: 	}
551: 
552: 	/* Enter Init mode inside the LL_RTC_Time and Date Init functions */
553: 	uint32_t hours = bin2bcd(timeptr->tm_hour);
554: 	uint32_t minutes = bin2bcd(timeptr->tm_min);
555: 	uint32_t seconds = bin2bcd(timeptr->tm_sec);
556: 
557: 	/* Set Date after Time to be sure the DR is correctly updated on stm32F2 serie. */
558: 	uint32_t year = bin2bcd((real_year - RTC_YEAR_REF));
559: 	uint32_t month = bin2bcd((timeptr->tm_mon + 1));
560: 	uint32_t day = bin2bcd(timeptr->tm_mday);
561: 	uint32_t weekDay = ((timeptr->tm_wday == 0) ? (LL_RTC_WEEKDAY_SUNDAY) : (timeptr->tm_wday));
562: 	/* WeekDay sunday (tm_wday = 0) is not represented by the same value in hardware,
563: 	 * all the other values are consistent with what is expected by hardware.
564: 	 */
565: 
566: 	LOG_DBG("Setting clock");
567: 
568: 	k_spinlock_key_t key = k_spin_lock(&data->lock);
569: 
570: 	stm32_backup_domain_enable_access();
571: 
572: 	/* Disable the write protection for RTC registers */
573: 	LL_RTC_DisableWriteProtection(RTC);
574: 
575: 	/* Set Initialization mode */
576: 	err = rtc_stm32_enter_init_mode();
577: 
578: 	if (err == 0) {
579: 		/* Set time and date */
580: 		LL_RTC_TIME_Config(RTC, LL_RTC_TIME_FORMAT_AM_OR_24, hours, minutes, seconds);
581: 		LL_RTC_DATE_Config(RTC, weekDay, day, month, year);
582: 	}
583: 
584: 	/* Exit Initialization mode */
585: 	LL_RTC_DisableInitMode(RTC);
586: 
587: 	/* Enable the write protection for RTC registers */
588: 	LL_RTC_EnableWriteProtection(RTC);
589: 
590: 	stm32_backup_domain_disable_access();
591: 
592: #ifdef CONFIG_SOC_SERIES_STM32F2X
593: 	/*
594: 	 * Because stm32F2 serie has no shadow registers,
595: 	 * wait until TR and DR registers are synchronised : flag RS
596: 	 */
597: 	while (LL_RTC_IsActiveFlag_RS(RTC) != 1) {
598: 		;
599: 	}
600: #endif /* CONFIG_SOC_SERIES_STM32F2X */
601: 
602: 	LOG_DBG("Calendar set : %d/%d/%d - %dh%dm%ds",
603: 			LL_RTC_DATE_GetDay(RTC),
604: 			LL_RTC_DATE_GetMonth(RTC),
605: 			LL_RTC_DATE_GetYear(RTC),
606: 			LL_RTC_TIME_GetHour(RTC),
607: 			LL_RTC_TIME_GetMinute(RTC),
608: 			LL_RTC_TIME_GetSecond(RTC)
609: 	);
610: 
611: 	k_spin_unlock(&data->lock, key);
612: 
613: 	return err;
614: }
615: 
616: static int rtc_stm32_get_time(const struct device *dev, struct rtc_time *timeptr)
617: {
618: 	struct rtc_stm32_data *data = dev->data;
619: 
620: 	uint32_t rtc_date, rtc_time;
621: 
622: #if HW_SUBSECOND_SUPPORT
623: 	const struct rtc_stm32_config *cfg = dev->config;
```

## tests/drivers/counter/counter_basic_api/src/test_counter.c

```c
979: /* Function checks if relative alarm set for 1 tick will expire. If handler is
980:  * not called within near future it indicates that driver do not support it and
981:  * more extensive testing is skipped.
982:  */
983: static bool short_relative_capable(const struct device *dev)
984: {
985: 	struct counter_alarm_cfg alarm_cfg = {
986: 		.callback = alarm_handler,
987: 		.flags = 0,
988: 		.user_data = NULL,
989: 		.ticks = 1
990: 	};
991: 	int err;
992: 	uint32_t cnt;
993: 	bool ret;
994: 
995: 	if (single_channel_alarm_capable(dev) == false) {
996: 		return false;
997: 	}
998: 
999: 	err = counter_start(dev);
1000: 	if (err != 0) {
1001: 		ret = false;
1002: 		goto end;
1003: 	}
1004: 
1005: 	k_sem_reset(&alarm_cnt_sem);
1006: 	alarm_cnt = 0;
1007: 	err = counter_set_channel_alarm(dev, 0, &alarm_cfg);
1008: 	if (err != 0) {
1009: 		ret = false;
1010: 		goto end;
1011: 	}
1012: 
1013: 	k_busy_wait(counter_ticks_to_us(dev, 10));
1014: 	cnt = IS_ENABLED(CONFIG_ZERO_LATENCY_IRQS) ?
1015: 			alarm_cnt : k_sem_count_get(&alarm_cnt_sem);
1016: 	if (cnt == 1) {
1017: 		ret = true;
1018: 	} else {
1019: 		ret = false;
1020: 		(void)counter_cancel_channel_alarm(dev, 0);
1021: 	}
1022: 
1023: end:
1024: 	k_sem_reset(&alarm_cnt_sem);
1025: 	alarm_cnt = 0;
1026: 	counter_stop(dev);
1027: 	k_busy_wait(1000);
1028: 
1029: 	return ret;
1030: }
1031: 
1032: ZTEST(counter_basic, test_short_relative_alarm)
1033: {
1034: 	test_all_instances(test_short_relative_alarm_instance,
1035: 			short_relative_capable);
1036: }
```
