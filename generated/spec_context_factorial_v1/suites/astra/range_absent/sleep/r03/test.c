#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define SLEEP_MS 2000
#define MARGIN_MS 1000

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper;
static struct k_sem ready;
static struct k_sem done;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;
static int64_t wake_ms;
static volatile bool isr_context;
static volatile bool wake_issued;
static volatile bool completed_after_wake;
static volatile bool completion_pending_at_wake;

static void sleeper_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);

	/* Starting early makes the measured sleep interval conservative. */
	sleep_start_ms = k_uptime_get();
	k_sem_give(&ready);
	/*
	 * This cooperative thread cannot be preempted by the test thread.
	 * On this single CPU, the test can consume ready only after we block
	 * here (or finish, which the checks below reject).
	 */
	k_sleep(K_MSEC(SLEEP_MS));
	sleep_end_ms = k_uptime_get();
	completed_after_wake = wake_issued;
	k_sem_give(&done);
}

static void wake_from_isr(const void *arg)
{
	ARG_UNUSED(arg);

	isr_context = k_is_in_isr();
	wake_ms = k_uptime_get();
	completion_pending_at_wake = (k_sem_count_get(&done) != 0U);
	wake_issued = true;
	k_wakeup(&sleeper);
}

ZTEST(sleep_wakeup, test_isr_wakes_sleeping_thread)
{
	k_sem_init(&ready, 0, 1);
	k_sem_init(&done, 0, 1);
	isr_context = false;
	wake_issued = false;
	completed_after_wake = false;
	completion_pending_at_wake = false;

	k_thread_create(&sleeper, sleeper_stack,
			K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper_entry,
			NULL, NULL, NULL, K_PRIO_COOP(0), 0, K_NO_WAIT);

	int ready_rc = k_sem_take(&ready, K_SECONDS(1));

	if (ready_rc != 0) {
		k_thread_abort(&sleeper);
	}
	zassert_equal(ready_rc, 0, "Sleeper did not become ready");

	irq_offload(wake_from_isr, NULL);

	/* Completion is observed through a semaphore, not a timing guess. */
	int done_rc = k_sem_take(&done, K_MSEC(500));

	if (done_rc != 0) {
		k_thread_abort(&sleeper);
	}
	zassert_equal(done_rc, 0, "Sleeper did not signal completion");
	zassert_equal(k_thread_join(&sleeper, K_SECONDS(1)), 0,
		      "Sleeper did not exit");

	zassert_true(isr_context, "Wakeup callback was not in an ISR");
	zassert_false(completion_pending_at_wake,
		      "Sleeper completed before wakeup");
	/*
	 * Together with the cooperative handoff, this deadline check proves
	 * the requested sleep had not expired when the ISR issued wakeup.
	 */
	zassert_true(wake_ms >= sleep_start_ms &&
		     wake_ms - sleep_start_ms < SLEEP_MS - MARGIN_MS,
		     "ISR missed the sleeping interval");
	zassert_true(completed_after_wake,
		     "Completion preceded ISR wakeup");
	zassert_true(sleep_end_ms >= wake_ms,
		     "Sleeper resumed before ISR wakeup");
	/*
	 * Require a full second of early return: a substantial margin over
	 * tick/millisecond rounding, while allowing ample dispatch latency.
	 */
	zassert_true(sleep_end_ms - sleep_start_ms < SLEEP_MS - MARGIN_MS,
		     "Sleep did not end sufficiently early");
}

ZTEST_SUITE(sleep_wakeup, NULL, NULL, NULL, NULL, NULL);
