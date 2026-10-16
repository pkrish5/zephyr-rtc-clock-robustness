#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define MESSAGE_SIZE 4
#define MESSAGE_COUNT 2

K_MSGQ_DEFINE(test_queue, MESSAGE_SIZE, MESSAGE_COUNT, 1);

static const uint8_t sent[MESSAGE_COUNT][MESSAGE_SIZE] = {
	{0x12, 0x34, 0x56, 0x78},
	{0xA5, 0x00, 0xFF, 0x5A},
};

static int put_result[MESSAGE_COUNT];
static bool ran_in_isr;

static void put_from_isr(const void *arg)
{
	(void)arg;
	ran_in_isr = k_is_in_isr();

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		/* Interrupt context must never request a blocking timeout. */
		put_result[i] = k_msgq_put(&test_queue, sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_thread_get)
{
	uint8_t received[MESSAGE_SIZE];

	zassert_false(k_is_in_isr(), "Retrieval must run in thread context");
	zassert_equal(k_msgq_num_used_get(&test_queue), 0U,
		      "Queue must initially be empty");

	ran_in_isr = false;
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		put_result[i] = -1;
	}

	/* Offload completes before returning; no clock-based delay is needed. */
	irq_offload(put_from_isr, NULL);

	zassert_true(ran_in_isr, "Callback did not run in interrupt context");
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(put_result[i], 0, "ISR put %d failed", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), MESSAGE_COUNT,
		      "Unexpected queue occupancy after ISR puts");

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(k_msgq_get(&test_queue, received, K_NO_WAIT), 0,
			      "Thread get %d failed", i);
		zassert_mem_equal(received, sent[i], MESSAGE_SIZE,
				  "Message %d bytes differ", i);
		zassert_equal(k_msgq_num_used_get(&test_queue),
			      MESSAGE_COUNT - i - 1,
			      "Unexpected queue occupancy after get %d", i);
	}

	zassert_equal(k_msgq_num_used_get(&test_queue), 0U,
		      "Queue must be empty after retrieval");
	/* HSI frequency accuracy alone provides no delivery-latency bound. */
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
