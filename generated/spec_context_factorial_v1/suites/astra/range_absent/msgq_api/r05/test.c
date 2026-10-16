#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

#define MSG_COUNT 2
#define MSG_SIZE 8

K_MSGQ_DEFINE(test_msgq, MSG_SIZE, MSG_COUNT, 4);

static const uint8_t messages[MSG_COUNT][MSG_SIZE] = {
	{0x00, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xff},
	{0xff, 0xed, 0xcb, 0xa9, 0x87, 0x65, 0x43, 0x00},
};

struct isr_result {
	bool in_isr;
	int put_rc[MSG_COUNT];
};

static void put_from_isr(const void *arg)
{
	struct isr_result *result = (struct isr_result *)arg;

	result->in_isr = k_is_in_isr();
	for (int i = 0; i < MSG_COUNT; ++i) {
		result->put_rc[i] = k_msgq_put(&test_msgq, messages[i],
					     K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_thread_get)
{
	struct isr_result result = {
		.in_isr = false,
		.put_rc = {-1, -1},
	};
	uint8_t received[MSG_SIZE];

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "Queue must initially be empty");

	irq_offload(put_from_isr, &result);

	zassert_true(result.in_isr, "Callback must run in ISR context");
	for (int i = 0; i < MSG_COUNT; ++i) {
		zassert_equal(result.put_rc[i], 0,
			      "Nonblocking ISR put %d failed", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), MSG_COUNT,
		      "Both messages must be queued");

	for (int i = 0; i < MSG_COUNT; ++i) {
		zassert_equal(k_msgq_get(&test_msgq, received, K_NO_WAIT), 0,
			      "Thread get %d failed", i);
		zassert_mem_equal(received, messages[i], MSG_SIZE,
				  "Message %d bytes differ", i);
		zassert_equal(k_msgq_num_used_get(&test_msgq),
			      MSG_COUNT - i - 1, "Unexpected queue count");
	}

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "Queue must be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
