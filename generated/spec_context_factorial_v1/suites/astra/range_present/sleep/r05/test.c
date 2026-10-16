#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define REQUESTED_SLEEP_MS 2000
#define EARLY_WAKE_LIMIT_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem started;
static struct k_sem completed;

static struct {
	int64_t sleep_start;
	int64_t sleep_end;
	int64_t irq_time;
	atomic_t resumed;
	atomic_t wakeup_issued;
	bool interrupt_context;
	bool not_resumed_at_irq;
	bool completion_after_wakeup;
} observation;

static void sleeper(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	observation.sleep_start = k_uptime_get();
	k_sem_give(&started);
	k_sleep(K_MSEC(REQUESTED_SLEEP_MS));
	observation.sleep_end = k_uptime_get();
	atomic_set(&observation.resumed, 1);
	observation.completion_after_wakeup =
		atomic_get(&observation.wakeup_issued) != 0;
	k_sem_give(&completed);
}

static void wakeup_isr(const void *arg)
{
	ARG_UNUSED(arg);

	observation.interrupt_context = k_is_in_isr();
	observation.irq_time = k_uptime_get();
	observation.not_resumed_at_irq =
		atomic_get(&observation.resumed) == 0;
	k_wakeup(&sleeper_thread);
	/* On this single CPU, the sleeper cannot run until ISR return. */
	atomic_set(&observation.wakeup_issued, 1);
}

ZTEST(sleep_wakeup, test_interrupt_wakes_sleeping_thread)
{
	k_tid_t controller = k_current_get();
	int original_priority = k_thread_priority_get(controller);
	int completion_result = -1;

	k_sem_init(&started, 0, 1);
	k_sem_init(&completed, 0, 1);
	observation.sleep_start = 0;
	observation.sleep_end = 0;
	observation.irq_time = 0;
	atomic_clear(&observation.resumed);
	atomic_clear(&observation.wakeup_issued);
	observation.interrupt_context = false;
	observation.not_resumed_at_irq = false;
	observation.completion_after_wakeup = false;

	/*
	 * The sleeper has strictly higher priority than the controller.
	 * Giving 'started' therefore cannot transfer execution to the
	 * controller. On one CPU, the controller can proceed only after
	 * the sleeper blocks in k_sleep() (or its sleep has already ended,
	 * which the ISR observations below explicitly reject).
	 */
	k_thread_priority_set(controller, K_PRIO_PREEMPT(1));
	k_thread_create(&sleeper_thread, sleeper_stack,
			K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
			NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);

	int start_result = k_sem_take(&started, K_MSEC(1000));

	if (start_result == 0) {
		irq_offload(wakeup_isr);
		completion_result = k_sem_take(&completed, K_MSEC(1000));
	}

	/* Clean up even when a synchronization deadline was missed. */
	k_thread_abort(&sleeper_thread);
	k_thread_priority_set(controller, original_priority);

	zassert_equal(start_result, 0, "Sleeper did not start");
	zassert_true(observation.interrupt_context,
		     "Wakeup callback was not in interrupt context");
	zassert_true(observation.not_resumed_at_irq,
		     "Sleeper had already resumed before the ISR");

	int64_t before_wakeup = observation.irq_time - observation.sleep_start;

	/* Reject an ISR arriving near or after the natural sleep expiry. */
	zassert_true(before_wakeup >= 0 &&
		     before_wakeup < EARLY_WAKE_LIMIT_MS,
		     "ISR did not arrive safely within the requested sleep");
	zassert_equal(completion_result, 0,
		      "Sleeper did not signal completion after wakeup");
	zassert_true(observation.completion_after_wakeup,
		     "Sleeper completed before the ISR issued wakeup");

	int64_t elapsed = observation.sleep_end - observation.sleep_start;

	/*
	 * Require at least 1000 ms of headroom against a 2000 ms sleep.
	 * Both times use kernel uptime; the measurement also includes the
	 * small pre-sleep semaphore overhead, making this conservative.
	 * The 1000 ms limit is an explicit test acceptance budget, not an
	 * ISR-delivery bound derived from the HSI's +/-1% accuracy. That
	 * frequency tolerance corresponds to roughly 20 ms over 2 seconds,
	 * far smaller than the chosen margin.
	 */
	zassert_true(elapsed >= 0 && elapsed < EARLY_WAKE_LIMIT_MS,
		     "Sleep was not shortened by the required margin");
}

ZTEST_SUITE(sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
