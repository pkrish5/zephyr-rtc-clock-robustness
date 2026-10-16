#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define REQUESTED_MS 1000

K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker_thread;
static struct k_sem ready;
static struct k_sem done;
static atomic_t resumed;
static atomic_t wake_issued;
static int64_t start_ms;
static int64_t elapsed_ms;
static int64_t margin_ms;
static bool interrupt_context;
static bool asleep_at_wakeup;
static bool completion_after_wakeup;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	start_ms = k_uptime_get();
	/*
	 * This cooperative thread cannot be preempted by the test thread.
	 * On this single CPU, the test can consume ready and continue only
	 * after this thread blocks in k_sleep(). No other thread wakes it.
	 */
	k_sem_give(&ready);
	k_sleep(K_MSEC(REQUESTED_MS));

	elapsed_ms = k_uptime_get() - start_ms;
	completion_after_wakeup = atomic_get(&wake_issued) != 0;
	atomic_set(&resumed, 1);
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	ARG_UNUSED(arg);
	int64_t since_start = k_uptime_get() - start_ms;

	interrupt_context = k_is_in_isr();
	/*
	 * The ready handshake establishes entry into sleep. Checking both
	 * noncompletion and a time safely before expiry excludes a natural
	 * timeout, including a thread whose timeout expired but has not run.
	 */
	asleep_at_wakeup = atomic_get(&resumed) == 0 &&
			   since_start < REQUESTED_MS - margin_ms;
	atomic_set(&wake_issued, 1);
	k_wakeup(&worker_thread);
}

ZTEST(sleep_wakeup, test_isr_wakes_sleeping_thread)
{
	int ready_result;
	int done_result;
	int64_t two_ticks_ms = 2 * (int64_t)k_ticks_to_ms_ceil64(1);

	/*
	 * Require at least 100 ms of early return (10% of the request),
	 * enlarged to two ticks if necessary to cover tick quantization.
	 * This exceeds the stated 1% HSI clock uncertainty. Both timestamps
	 * use the same uptime clock. The margin is an executable acceptance
	 * criterion, not an ISR delivery bound inferred from HSI accuracy.
	 */
	margin_ms = two_ticks_ms > 100 ? two_ticks_ms : 100;
	zassert_true(margin_ms < REQUESTED_MS / 2,
		     "System tick is too coarse for this timing test");

	k_sem_init(&ready, 0, 1);
	k_sem_init(&done, 0, 1);
	atomic_clear(&resumed);
	atomic_clear(&wake_issued);
	interrupt_context = false;
	asleep_at_wakeup = false;
	completion_after_wakeup = false;
	elapsed_ms = REQUESTED_MS;

	k_thread_create(&worker_thread, worker_stack,
			K_THREAD_STACK_SIZEOF(worker_stack), sleeper,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	ready_result = k_sem_take(&ready, K_MSEC(1500));
	if (ready_result != 0) {
		k_thread_abort(&worker_thread);
		zassert_equal(ready_result, 0, "Sleeper did not become ready");
		return;
	}

	irq_offload(wake_from_isr, NULL);
	done_result = k_sem_take(&done, K_MSEC(1500));
	/* Clean up even on failure, before any assertion can exit the test. */
	k_thread_abort(&worker_thread);

	zassert_true(interrupt_context, "Wakeup was not issued in an ISR");
	zassert_true(asleep_at_wakeup, "Target was not safely within its sleep");
	zassert_equal(done_result, 0, "Sleeper did not signal completion");
	zassert_true(completion_after_wakeup,
		     "Sleeper completed before the ISR wakeup");
	zassert_true(elapsed_ms >= 0 &&
		     elapsed_ms < REQUESTED_MS - margin_ms,
		     "Sleep lasted %lld ms; required less than %lld ms",
		     (long long)elapsed_ms,
		     (long long)(REQUESTED_MS - margin_ms));
}

ZTEST_SUITE(sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
