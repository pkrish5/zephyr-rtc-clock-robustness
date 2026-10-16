#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define MSG_SIZE 4
#define MSG_COUNT 2

K_MSGQ_DEFINE(test_msgq, MSG_SIZE, MSG_COUNT, 1);

static const uint8_t sent[MSG_COUNT][MSG_SIZE] = {
	{ 0x12, 0x34, 0x56, 0x78 },
	{ 0xA5, 0x5A, 0xC3, 0x3C },
};

struct isr_result {
	int put_status[MSG_COUNT];
};

static void put_from_isr(const void *arg)
{
	struct isr_result *result = (struct isr_result *)arg;

	for (int i = 0; i < MSG_COUNT; ++i) {
		result->put_status[i] = k_msgq_put(&test_msgq, sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_to_thread_messages)
{
	struct isr_result result = { 0 };
	uint8_t received[MSG_SIZE];

	k_msgq_purge(&test_msgq);
	irq_offload(put_from_isr, &result);

	for (int i = 0; i < MSG_COUNT; ++i) {
		zassert_equal(result.put_status[i], 0, "ISR put %d failed", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), MSG_COUNT,
		      "unexpected number of queued messages");

	for (int i = 0; i < MSG_COUNT; ++i) {
		zassert_equal(k_msgq_get(&test_msgq, received, K_NO_WAIT), 0,
			      "get %d failed", i);
		for (int j = 0; j < MSG_SIZE; ++j) {
			zassert_equal(received[j], sent[i][j],
				      "message %d byte %d differs", i, j);
		}
	}

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "queue is not empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
