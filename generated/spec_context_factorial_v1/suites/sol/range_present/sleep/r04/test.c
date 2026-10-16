#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP_MS 2000
#define EARLY_LIMIT_MS 1500

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper;
static K_SEM_DEFINE(ready, 0, 1);
static K_SEM_DEFINE(done, 0, 1);
static atomic_t wakeup_was_in_isr;
static int64_t elapsed_ms;

static void sleep_thread(void *a, void *b, void *c)
{
	int64_t start;

	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_sem_give(&ready);
	start = k_uptime_get();
	k_sleep(K_MSEC(REQUESTED_SLEEP_MS));
	elapsed_ms = k_uptime_get() - start;
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	atomic_set(&wakeup_was_in_isr, k_is_in_isr());
	k_wakeup((k_tid_t)arg);
}

ZTEST(wakeup, test_sleeping_thread_woken_from_isr)
{
	k_tid_t tid = k_thread_create(&sleeper, sleeper_stack,
				     K_THREAD_STACK_SIZEOF(sleeper_stack),
				     sleep_thread, NULL, NULL, NULL,
				     K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&ready, K_MSEC(500)));

	/* On this single CPU, sleeping here lets the ready thread enter k_sleep(). */
	k_sleep(K_MSEC(50));
	zassert_equal(k_sem_count_get(&done), 0);

	irq_offload(wake_from_isr, tid);
	zassert_equal(atomic_get(&wakeup_was_in_isr), 1);
	zassert_ok(k_sem_take(&done, K_MSEC(1000)));

	/* 500 ms of headroom exceeds the clock's 1% error over two seconds. */
	zassert_true(elapsed_ms >= 0 && elapsed_ms < EARLY_LIMIT_MS,
		     "sleep lasted %lld ms", (long long)elapsed_ms);
}

ZTEST_SUITE(wakeup, NULL, NULL, NULL, NULL, NULL);
