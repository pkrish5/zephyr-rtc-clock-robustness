#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

ZTEST(timer_expiry, test_periodic_timer_expirations)
{
	static struct k_timer timer;
	uint32_t observed = 0U;

	k_timer_init(&timer, NULL, NULL);
	k_timer_start(&timer, K_MSEC(10), K_MSEC(10));

	for (int i = 0; i < 2; ++i) {
		uint32_t expirations = k_timer_status_sync(&timer);

		zassert_true(expirations > 0U, "timer synchronization returned no expirations");
		observed += expirations;
	}

	zassert_true(observed >= 2U, "expected at least two timer expirations");
	zassert_true(k_timer_remaining_get(&timer) > 0,
		     "periodic timer should remain active after expirations");

	k_timer_stop(&timer);
	zassert_equal(k_timer_status_sync(&timer), 0U,
		      "stopped timer should have no pending expirations");
}

ZTEST_SUITE(timer_expiry, NULL, NULL, NULL, NULL, NULL);
