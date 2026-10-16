#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define MESSAGE_COUNT 2
#define MESSAGE_SIZE 4

K_MSGQ_DEFINE(test_queue, MESSAGE_SIZE, MESSAGE_COUNT, 4);

static const uint8_t messages[MESSAGE_COUNT][MESSAGE_SIZE] = {
	{ 0x12, 0x34, 0x56, 0x78 },
	{ 0xAB, 0xCD, 0xEF, 0x90 },
};
static int put_results[MESSAGE_COUNT];
static bool ran_in_isr;

static void put_from_isr(const void *unused)
{
	(void)unused;
	ran_in_isr = k_is_in_isr();

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		put_results[i] = k_msgq_put(&test_queue, messages[i], K_NO_WAIT);
	}
}

ZTEST(msgq_irq, test_isr_put_thread_get)
{
	uint8_t received[MESSAGE_SIZE];

	k_msgq_purge(&test_queue);
	ran_in_isr = false;
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		put_results[i] = -1;
	}

	irq_offload(put_from_isr, NULL);

	zassert_true(ran_in_isr, "Callback must run in interrupt context");
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(put_results[i], 0, "ISR put %d failed", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), MESSAGE_COUNT,
		      "Unexpected queue occupancy after ISR puts");

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_ok(k_msgq_get(&test_queue, received, K_NO_WAIT),
			   "Thread get %d failed", i);
		zassert_mem_equal(received, messages[i], MESSAGE_SIZE,
				  "Message %d differs from ISR data", i);
	}

	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "Queue must be empty after retrieval");
}

ZTEST_SUITE(msgq_irq, NULL, NULL, NULL, NULL, NULL);
