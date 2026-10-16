#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define MESSAGE_SIZE 8
#define MESSAGE_COUNT 2

K_MSGQ_DEFINE(test_queue, MESSAGE_SIZE, MESSAGE_COUNT, 1);

static const uint8_t messages[MESSAGE_COUNT][MESSAGE_SIZE] = {
	{ 0x00, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xff },
	{ 0xff, 0xed, 0xcb, 0xa9, 0x87, 0x65, 0x43, 0x00 },
};
static int put_results[MESSAGE_COUNT];
static int observed_isr;

static void put_from_isr(const void *arg)
{
	(void)arg;
	observed_isr = k_is_in_isr();

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		put_results[i] = k_msgq_put(&test_queue, messages[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_thread_get)
{
	uint8_t received[MESSAGE_SIZE];

	k_msgq_purge(&test_queue);
	observed_isr = 0;
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		put_results[i] = -1;
	}

	irq_offload(put_from_isr, NULL);

	zassert_true(observed_isr, "Callback must execute in ISR context");
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(put_results[i], 0,
			      "Nonblocking ISR put %d failed: %d", i, put_results[i]);
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), MESSAGE_COUNT,
		      "Unexpected queued message count");

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_ok(k_msgq_get(&test_queue, received, K_NO_WAIT),
			   "Thread get %d failed", i);
		zassert_mem_equal(received, messages[i], MESSAGE_SIZE,
				  "Message %d differs from ISR data", i);
	}

	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "Queue must be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
