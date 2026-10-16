#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

ZTEST(timer_periodic, test_periodic_expiry_and_stop)
{
	struct k_timer timer;
	const k_timeout_t period = K_MSEC(20);

	k_timer_init(&timer, NULL, NULL);
	k_timer_start(&timer, period, period);

	for (int i = 0; i < 2; ++i) {
		uint32_t expirations = k_timer_status_sync(&timer);

		zassert_true(expirations > 0U,
			     "timer synchronization returned no expirations");
	}

	zassert_true(k_timer_remaining_get(&timer) > 0,
		     "periodic timer is not active after expirations");

	k_timer_stop(&timer);
	zassert_equal(k_timer_status_sync(&timer), 0U,
		      "stopped timer reported an expiry");
}

ZTEST_SUITE(timer_periodic, NULL, NULL, NULL, NULL, NULL);
