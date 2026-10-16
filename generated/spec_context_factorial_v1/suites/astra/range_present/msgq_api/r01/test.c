#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define MESSAGE_COUNT 2
#define MESSAGE_SIZE 8

static const uint8_t messages[MESSAGE_COUNT][MESSAGE_SIZE] = {
	{ 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77 },
	{ 0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88 },
};

K_MSGQ_DEFINE(test_queue, MESSAGE_SIZE, MESSAGE_COUNT, 4);

struct isr_results {
	bool ran_in_isr;
	int put_status[MESSAGE_COUNT];
};

static void put_from_isr(const void *arg)
{
	struct isr_results *results = (struct isr_results *)arg;

	results->ran_in_isr = k_is_in_isr();
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		/* ISR operations must never request a blocking timeout. */
		results->put_status[i] =
			k_msgq_put(&test_queue, messages[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_thread_get)
{
	struct isr_results results = {
		.ran_in_isr = false,
		.put_status = { -1, -1 },
	};
	uint8_t received[MESSAGE_SIZE];

	k_msgq_purge(&test_queue);
	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "Queue must start empty");

	/* irq_offload completes the callback before returning. */
	irq_offload(put_from_isr, &results);

	zassert_true(results.ran_in_isr, "Callback must execute in ISR context");
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(results.put_status[i], 0,
			      "Nonblocking ISR put %d failed", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), MESSAGE_COUNT,
		      "Unexpected queued message count");

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(k_msgq_get(&test_queue, received, K_NO_WAIT), 0,
			      "Thread get %d failed", i);
		zassert_mem_equal(received, messages[i], MESSAGE_SIZE,
				  "Message %d bytes or FIFO order incorrect", i);
		zassert_equal(k_msgq_num_used_get(&test_queue),
			      MESSAGE_COUNT - i - 1,
			      "Unexpected queue state after retrieval");
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "Queue must be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
