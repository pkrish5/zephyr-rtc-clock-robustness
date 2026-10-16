#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define SLEEP_TIME K_SECONDS(5)

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem ready;
static struct k_sem done;
static atomic_t sleep_started;
static atomic_t sleep_finished;
static atomic_t woke_in_isr;
static atomic_t target_asleep_at_wakeup;
static int64_t elapsed_ms;

static void sleeper(void *a, void *b, void *c)
{
	int64_t start;

	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	start = k_uptime_get();
	atomic_set(&sleep_started, 1);
	k_sem_give(&ready);
	k_sleep(SLEEP_TIME);
	elapsed_ms = k_uptime_get() - start;
	atomic_set(&sleep_finished, 1);
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	atomic_set(&woke_in_isr, k_is_in_isr());
	atomic_set(&target_asleep_at_wakeup,
		   atomic_get(&sleep_started) && !atomic_get(&sleep_finished));
	k_wakeup((k_tid_t)arg);
}

ZTEST(k_wakeup_isr, wakes_sleeping_thread)
{
	k_tid_t tid;

	k_sem_init(&ready, 0, 1);
	k_sem_init(&done, 0, 1);
	atomic_clear(&sleep_started);
	atomic_clear(&sleep_finished);
	atomic_clear(&woke_in_isr);
	atomic_clear(&target_asleep_at_wakeup);

	tid = k_thread_create(&sleeper_thread, sleeper_stack,
			      K_THREAD_STACK_SIZEOF(sleeper_stack),
			      sleeper, NULL, NULL, NULL,
			      K_PRIO_PREEMPT(0), 0, K_NO_WAIT);
	zassert_ok(k_sem_take(&ready, K_SECONDS(1)));

	/* Yield the CPU long enough for the worker to enter k_sleep(). */
	k_sleep(K_MSEC(100));
	zassert_not_equal(atomic_get(&sleep_started), 0);
	zassert_equal(k_sem_take(&done, K_NO_WAIT), -EBUSY);

	irq_offload(wake_from_isr, tid);
	zassert_not_equal(atomic_get(&woke_in_isr), 0);
	zassert_not_equal(atomic_get(&target_asleep_at_wakeup), 0);
	zassert_ok(k_sem_take(&done, K_SECONDS(3)));
	zassert_ok(k_thread_join(tid, K_SECONDS(1)));

	/* Wakeup is requested after about 100 ms; the 4 s limit leaves
	 * ample scheduling margin and exceeds the 1% clock uncertainty.
	 */
	zassert_true(elapsed_ms < 4000,
		     "sleep lasted %lld ms", (long long)elapsed_ms);
}

ZTEST_SUITE(k_wakeup_isr, NULL, NULL, NULL, NULL, NULL);
