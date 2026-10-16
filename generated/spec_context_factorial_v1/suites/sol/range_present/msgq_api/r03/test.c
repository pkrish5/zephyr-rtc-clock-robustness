#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define MSG_COUNT 2
#define MSG_SIZE 4

K_MSGQ_DEFINE(test_msgq, MSG_SIZE, MSG_COUNT, 4);

static const uint8_t sent[MSG_COUNT][MSG_SIZE] = {
	{0x12, 0x34, 0x56, 0x78},
	{0xa5, 0x5a, 0x00, 0xff},
};

static int put_result[MSG_COUNT];
static bool ran_in_isr;

static void put_messages_from_isr(const void *arg)
{
	(void)arg;
	ran_in_isr = k_is_in_isr();

	for (int i = 0; i < MSG_COUNT; i++) {
		put_result[i] = k_msgq_put(&test_msgq, sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_put_from_isr_get_from_thread)
{
	uint8_t received[MSG_SIZE];

	k_msgq_purge(&test_msgq);
	ran_in_isr = false;
	irq_offload(put_messages_from_isr, NULL);

	zassert_true(ran_in_isr, "callback did not run in ISR context");
	for (int i = 0; i < MSG_COUNT; i++) {
		zassert_ok(put_result[i], "ISR put failed for message %d", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), MSG_COUNT,
		      "unexpected queue depth after ISR puts");

	for (int i = 0; i < MSG_COUNT; i++) {
		zassert_ok(k_msgq_get(&test_msgq, received, K_NO_WAIT),
			   "get failed for message %d", i);
		zassert_mem_equal(received, sent[i], MSG_SIZE,
				  "message %d differs", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "queue is not empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
