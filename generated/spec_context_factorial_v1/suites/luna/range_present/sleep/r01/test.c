#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define REQUESTED_SLEEP_MS 3000
#define WAKE_DELAY_MS 100
/* Allow 1 s beyond the intended wake point for scheduling and measurement. */
#define EARLY_WAKE_MARGIN_MS 1000
#define COMPLETION_TIMEOUT_MS (REQUESTED_SLEEP_MS + 2000)

K_THREAD_STACK_DEFINE(wakeup_stack, 1024);

static struct k_thread wakeup_thread;
static struct k_sem thread_started;
static struct k_sem thread_completed;
static volatile bool thread_entering_sleep;
static volatile bool isr_ran_in_interrupt;
static volatile bool isr_observed_sleep_phase;
static int64_t observed_sleep_ms;

static void sleeping_thread(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	k_sem_give(&thread_started);
	int64_t start_ms = k_uptime_get();
	thread_entering_sleep = true;
	(void)k_sleep(K_MSEC(REQUESTED_SLEEP_MS));
	observed_sleep_ms = k_uptime_get() - start_ms;
	k_sem_give(&thread_completed);
}

static void wakeup_isr(const void *unused)
{
	ARG_UNUSED(unused);
	isr_ran_in_interrupt = k_is_in_isr();
	isr_observed_sleep_phase = thread_entering_sleep;
	k_wakeup(&wakeup_thread);
}

ZTEST(k_wakeup_from_isr, test_wakeup_sleeping_thread)
{
	k_sem_init(&thread_started, 0, 1);
	k_sem_init(&thread_completed, 0, 1);
	thread_entering_sleep = false;
	isr_ran_in_interrupt = false;
	isr_observed_sleep_phase = false;
	observed_sleep_ms = -1;

	k_thread_create(&wakeup_thread, wakeup_stack,
			K_THREAD_STACK_SIZEOF(wakeup_stack), sleeping_thread,
			NULL, NULL, NULL, K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&thread_started, K_SECONDS(1)),
		   "worker did not start");
	/* Let the worker run into k_sleep before arranging the interrupt. */
	k_sleep(K_MSEC(WAKE_DELAY_MS));
	irq_offload(wakeup_isr, NULL);

	zassert_ok(k_sem_take(&thread_completed, K_MSEC(COMPLETION_TIMEOUT_MS)),
		   "worker did not complete after the ISR wakeup");
	zassert_true(isr_ran_in_interrupt, "wakeup callback did not run in ISR context");
	zassert_true(isr_observed_sleep_phase,
		    "wakeup was not issued after the worker entered its sleep phase");
	zassert_true(observed_sleep_ms >= 0, "worker did not report its sleep duration");
	zassert_true(observed_sleep_ms < REQUESTED_SLEEP_MS - EARLY_WAKE_MARGIN_MS,
		    "sleep was not shortened by the expected margin: %lld ms",
		    (long long)observed_sleep_ms);

	k_thread_abort(&wakeup_thread);
}

ZTEST_SUITE(k_wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
