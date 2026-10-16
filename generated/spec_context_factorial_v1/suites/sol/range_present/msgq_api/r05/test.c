#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define MSG_SIZE 4
#define MSG_COUNT 2

K_MSGQ_DEFINE(test_queue, MSG_SIZE, MSG_COUNT, 4);

static const uint8_t sent[MSG_COUNT][MSG_SIZE] = {
	{0x12, 0x34, 0x56, 0x78},
	{0xA5, 0x5A, 0xC3, 0x3C},
};
static int put_result[MSG_COUNT];

static void put_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	for (int i = 0; i < MSG_COUNT; i++) {
		put_result[i] = k_msgq_put(&test_queue, sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_put_from_isr_and_get_from_thread)
{
	uint8_t received[MSG_SIZE];

	zassert_equal(k_msgq_num_used_get(&test_queue), 0);
	irq_offload(put_from_isr, NULL);

	for (int i = 0; i < MSG_COUNT; i++) {
		zassert_equal(put_result[i], 0, "ISR put failed");
		zassert_equal(k_msgq_get(&test_queue, received, K_NO_WAIT), 0,
			      "message get failed");
		zassert_mem_equal(received, sent[i], MSG_SIZE,
				  "retrieved message differs");
	}

	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "queue is not empty");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
