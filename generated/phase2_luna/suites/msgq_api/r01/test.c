#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct test_msg {
	uint32_t value;
};

K_MSGQ_DEFINE(test_msgq, sizeof(struct test_msg), 2, 4);

static const struct test_msg sent_msgs[] = {
	{ .value = 0x12345678U },
	{ .value = 0xA5A55A5AU },
};
static volatile int isr_put_results[ARRAY_SIZE(sent_msgs)];

static void put_messages_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	for (size_t i = 0; i < ARRAY_SIZE(sent_msgs); i++) {
		isr_put_results[i] = k_msgq_put(&test_msgq, &sent_msgs[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_and_thread_get)
{
	struct test_msg received;

	k_msgq_purge(&test_msgq);
	for (size_t i = 0; i < ARRAY_SIZE(sent_msgs); i++) {
		isr_put_results[i] = -1;
	}

	irq_offload(put_messages_from_isr, NULL);

	for (size_t i = 0; i < ARRAY_SIZE(sent_msgs); i++) {
		zassert_equal(isr_put_results[i], 0, "ISR put %zu failed", i);
		zassert_ok(k_msgq_get(&test_msgq, &received, K_NO_WAIT),
			   "thread get %zu failed", i);
		zassert_mem_equal(&received, &sent_msgs[i], sizeof(received),
				  "message %zu differs", i);
	}

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "queue should be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
