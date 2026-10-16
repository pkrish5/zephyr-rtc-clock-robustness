#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define MESSAGE_COUNT 2U
#define MESSAGE_SIZE 8U

K_MSGQ_DEFINE(isr_msgq, MESSAGE_SIZE, MESSAGE_COUNT, 1);

static const uint8_t sent[MESSAGE_COUNT][MESSAGE_SIZE] = {
	{ 0x00, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xff },
	{ 0xff, 0xed, 0xcb, 0xa9, 0x87, 0x65, 0x43, 0x00 },
};

struct isr_result {
	int in_isr;
	int put_status[MESSAGE_COUNT];
};

static void put_from_isr(const void *arg)
{
	struct isr_result *result = (struct isr_result *)arg;

	result->in_isr = k_is_in_isr();
	for (unsigned int i = 0; i < MESSAGE_COUNT; ++i) {
		/* Interrupt context must never request a blocking timeout. */
		result->put_status[i] = k_msgq_put(&isr_msgq, sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_thread_get)
{
	struct isr_result result = {
		.in_isr = 0,
		.put_status = { -1, -1 },
	};
	uint8_t received[MESSAGE_SIZE];

	zassert_false(k_is_in_isr(), "Retrieval must run in thread context");
	zassert_equal(k_msgq_num_used_get(&isr_msgq), 0U,
		      "Queue must start empty");

	/* irq_offload returns after the ISR callback has completed. */
	irq_offload(put_from_isr, &result);

	zassert_true(result.in_isr, "Callback did not execute in ISR context");
	for (unsigned int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(result.put_status[i], 0,
			      "Nonblocking ISR put %u failed", i);
	}
	zassert_equal(k_msgq_num_used_get(&isr_msgq), MESSAGE_COUNT,
		      "Unexpected queued message count");

	for (unsigned int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(k_msgq_get(&isr_msgq, received, K_NO_WAIT), 0,
			      "Thread get %u failed", i);
		zassert_mem_equal(received, sent[i], MESSAGE_SIZE,
				  "Message %u bytes or FIFO order differ", i);
		zassert_equal(k_msgq_num_used_get(&isr_msgq),
			      MESSAGE_COUNT - i - 1U,
			      "Unexpected queue occupancy after retrieval");
	}

	zassert_equal(k_msgq_num_used_get(&isr_msgq), 0U,
		      "Queue must be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
