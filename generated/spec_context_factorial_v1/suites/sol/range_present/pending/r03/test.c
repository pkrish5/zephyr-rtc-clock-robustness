#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <stdint.h>

K_THREAD_STACK_DEFINE(worker_stack, 1024);
K_SEM_DEFINE(worker_ready, 0, 1);
K_SEM_DEFINE(worker_done, 0, 1);

static struct k_thread worker_thread;
static struct k_timer timer;
static uint32_t expiration_count;

static void timer_worker(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_sem_give(&worker_ready);
	expiration_count = k_timer_status_sync(&timer);
	k_sem_give(&worker_done);
}

ZTEST(timer_wait, test_one_shot_expiry_wakes_worker)
{
	k_timer_init(&timer, NULL, NULL);
	k_timer_start(&timer, K_MSEC(1000), K_NO_WAIT);

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), timer_worker,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&worker_ready, K_SECONDS(2)));
	/* The cooperative worker runs through status_sync before this thread resumes. */
	zassert_true(k_timer_remaining_get(&timer) > 0U);
	zassert_not_equal(k_sem_take(&worker_done, K_NO_WAIT), 0);

	zassert_ok(k_sem_take(&worker_done, K_SECONDS(10)));
	zassert_equal(expiration_count, 1U);
	zassert_ok(k_thread_join(&worker_thread, K_SECONDS(1)));
}

ZTEST_SUITE(timer_wait, NULL, NULL, NULL, NULL, NULL);
