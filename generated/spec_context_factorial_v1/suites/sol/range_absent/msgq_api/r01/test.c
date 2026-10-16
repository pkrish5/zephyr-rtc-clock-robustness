#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>
#include <string.h>

#define MESSAGE_COUNT 2
#define MESSAGE_SIZE 4

K_MSGQ_DEFINE(test_msgq, MESSAGE_SIZE, MESSAGE_COUNT, 4);

static const uint8_t sent[MESSAGE_COUNT][MESSAGE_SIZE] = {
	{0x10, 0x21, 0x32, 0x43},
	{0xa5, 0xb6, 0xc7, 0xd8},
};

struct isr_results {
	int put_status[MESSAGE_COUNT];
};

static void put_from_isr(const void *arg)
{
	struct isr_results *results = (struct isr_results *)arg;

	for (int i = 0; i < MESSAGE_COUNT; i++) {
		results->put_status[i] = k_msgq_put(&test_msgq, sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_put_from_isr_get_from_thread)
{
	struct isr_results results;
	uint8_t received[MESSAGE_SIZE];

	k_msgq_purge(&test_msgq);
	irq_offload(put_from_isr, &results);

	for (int i = 0; i < MESSAGE_COUNT; i++) {
		zassert_equal(results.put_status[i], 0, "ISR put failed");
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), MESSAGE_COUNT,
		      "unexpected queue occupancy");

	for (int i = 0; i < MESSAGE_COUNT; i++) {
		zassert_equal(k_msgq_get(&test_msgq, received, K_NO_WAIT), 0,
			      "thread get failed");
		zassert_equal(memcmp(received, sent[i], MESSAGE_SIZE), 0,
			      "message bytes differ");
	}

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0U,
		      "queue is not empty");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
