#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <string.h>

struct message {
	uint8_t bytes[4];
};

K_MSGQ_DEFINE(test_msgq, sizeof(struct message), 2, 1);

static const struct message sent_messages[] = {
	{ .bytes = { 0x12, 0x34, 0x56, 0x78 } },
	{ .bytes = { 0x9a, 0xbc, 0xde, 0xf0 } },
};
static int isr_put_results[ARRAY_SIZE(sent_messages)];

static void put_messages_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	for (size_t i = 0; i < ARRAY_SIZE(sent_messages); i++) {
		isr_put_results[i] = k_msgq_put(&test_msgq, &sent_messages[i], K_NO_WAIT);
	}
}

ZTEST(msgq_irq, test_isr_put_and_thread_get)
{
	struct message received;

	k_msgq_purge(&test_msgq);
	memset(isr_put_results, 0xff, sizeof(isr_put_results));

	irq_offload(put_messages_from_isr, NULL);

	for (size_t i = 0; i < ARRAY_SIZE(sent_messages); i++) {
		zassert_equal(isr_put_results[i], 0, "ISR put %u failed: %d", (unsigned int)i,
			      isr_put_results[i]);
		zassert_ok(k_msgq_get(&test_msgq, &received, K_NO_WAIT),
			   "thread get %u failed", (unsigned int)i);
		zassert_mem_equal(&received, &sent_messages[i], sizeof(received),
				  "message %u differs", (unsigned int)i);
	}

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "queue should be empty after retrieval");
}

ZTEST_SUITE(msgq_irq, NULL, NULL, NULL, NULL, NULL);
