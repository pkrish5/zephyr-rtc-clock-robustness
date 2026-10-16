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

struct isr_results {
	bool in_isr;
	int put_rc[MESSAGE_COUNT];
};

static void put_from_isr(const void *arg)
{
	struct isr_results *results = (struct isr_results *)arg;

	results->in_isr = k_is_in_isr();
	for (unsigned int i = 0; i < MESSAGE_COUNT; ++i) {
		results->put_rc[i] = k_msgq_put(&test_queue, messages[i],
					      K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_thread_get)
{
	struct isr_results results = {
		.in_isr = false,
		.put_rc = { -1, -1 },
	};
	uint8_t received[MESSAGE_SIZE];

	zassert_false(k_is_in_isr(), "Receiver must run in thread context");
	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "Queue must initially be empty");

	irq_offload(put_from_isr, &results);

	zassert_true(results.in_isr, "Producer must run in ISR context");
	for (unsigned int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(results.put_rc[i], 0,
			      "Nonblocking ISR put failed for message %u", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), MESSAGE_COUNT,
		      "Unexpected queue occupancy after ISR puts");

	for (unsigned int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(k_msgq_get(&test_queue, received, K_NO_WAIT), 0,
			      "Thread get failed for message %u", i);
		zassert_mem_equal(received, messages[i], MESSAGE_SIZE,
				  "Message %u bytes differ", i);
	}

	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "Queue must be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
