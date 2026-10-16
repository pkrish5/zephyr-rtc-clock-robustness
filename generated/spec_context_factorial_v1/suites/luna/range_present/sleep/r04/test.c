#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define TARGET_SLEEP_MS 1000
#define WAKE_DELAY_MS 100
#define MIN_EARLY_MARGIN_MS 50
#define SEM_TIMEOUT_MS (TARGET_SLEEP_MS + 2000)
#define THREAD_PRIORITY 5

K_THREAD_STACK_DEFINE(sleeper_stack, 1024);
static struct k_thread sleeper_thread;
static struct k_sem started_sem;
static struct k_sem done_sem;
static int64_t sleep_start_ms;
static int64_t sleep_end_ms;

static void sleeper(void *a, void *b, void *c)
{
	ARG_UNUSED(a);
	ARG_UNUSED(b);
	ARG_UNUSED(c);

	k_sem_give(&started_sem);
	sleep_start_ms = k_uptime_get();
	k_sleep(K_MSEC(TARGET_SLEEP_MS));
	sleep_end_ms = k_uptime_get();
	k_sem_give(&done_sem);
}

static void wake_from_isr(const void *unused)
{
	ARG_UNUSED(unused);
	k_wakeup(&sleeper_thread);
}

ZTEST(wakeup_from_isr, test_wakeup_interrupts_sleep)
{
	k_sem_init(&started_sem, 0, 1);
	k_sem_init(&done_sem, 0, 1);

	k_thread_create(&sleeper_thread, sleeper_stack,
			K_THREAD_STACK_SIZEOF(sleeper_stack), sleeper,
			NULL, NULL, NULL, THREAD_PRIORITY, 0, K_NO_WAIT);

	zassert_ok(k_sem_take(&started_sem, K_SECONDS(2)),
		   "sleeper did not start");

	/* Allow the target to enter k_sleep before delivering the offloaded IRQ. */
	k_msleep(WAKE_DELAY_MS);
	irq_offload(wake_from_isr, NULL);

	zassert_ok(k_sem_take(&done_sem, K_MSEC(SEM_TIMEOUT_MS)),
		   "sleeper did not report completion after ISR wakeup");

	int64_t elapsed_ms = sleep_end_ms - sleep_start_ms;
	zassert_true(elapsed_ms < TARGET_SLEEP_MS - MIN_EARLY_MARGIN_MS,
		     "sleep duration %lld ms was not at least %d ms shorter than %d ms",
		     (long long)elapsed_ms, MIN_EARLY_MARGIN_MS, TARGET_SLEEP_MS);
}

ZTEST_SUITE(wakeup_from_isr, NULL, NULL, NULL, NULL, NULL);
