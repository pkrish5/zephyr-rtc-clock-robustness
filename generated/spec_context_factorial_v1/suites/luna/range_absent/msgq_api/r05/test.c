#include <zephyr/ztest.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>

#define MSG_SIZE 4
#define MSG_COUNT 2

K_MSGQ_DEFINE(test_msgq, MSG_SIZE, MSG_COUNT, 1);

static const uint8_t sent[MSG_COUNT][MSG_SIZE] = {
	{ 0x12, 0x34, 0x56, 0x78 },
	{ 0x9a, 0xbc, 0xde, 0xf0 },
};
static int isr_put_results[MSG_COUNT];

static void put_messages_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	for (size_t i = 0; i < MSG_COUNT; ++i) {
		isr_put_results[i] = k_msgq_put(&test_msgq, sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_and_thread_get)
{
	uint8_t received[MSG_SIZE];

	k_msgq_purge(&test_msgq);
	irq_offload(put_messages_from_isr, NULL);

	for (size_t i = 0; i < MSG_COUNT; ++i) {
		zassert_equal(isr_put_results[i], 0, "ISR put %u failed", (unsigned int)i);
		zassert_ok(k_msgq_get(&test_msgq, received, K_NO_WAIT), "thread get %u failed",
			   (unsigned int)i);
		zassert_mem_equal(received, sent[i], MSG_SIZE, "message %u differs",
				  (unsigned int)i);
	}

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0, "queue should be empty");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
