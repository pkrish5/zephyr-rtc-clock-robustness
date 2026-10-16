#include <zephyr/ztest.h>
#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>
#include <string.h>

struct message {
	uint32_t value;
	uint8_t tag;
};

K_MSGQ_DEFINE(test_msgq, sizeof(struct message), 2, 4);

static const struct message sent[] = {
	{ .value = 0x13579BDFU, .tag = 0x2AU },
	{ .value = 0x2468ACE0U, .tag = 0xC5U },
};
static volatile int isr_put_results[ARRAY_SIZE(sent)];

static void put_messages_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	for (size_t i = 0; i < ARRAY_SIZE(sent); ++i) {
		isr_put_results[i] = k_msgq_put(&test_msgq, &sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_nonblocking_isr_put_and_thread_get)
{
	struct message received;

	k_msgq_purge(&test_msgq);
	for (size_t i = 0; i < ARRAY_SIZE(sent); ++i) {
		isr_put_results[i] = -1;
	}

	irq_offload(put_messages_from_isr, NULL);

	for (size_t i = 0; i < ARRAY_SIZE(sent); ++i) {
		zassert_equal(isr_put_results[i], 0, "ISR put %u failed", (unsigned int)i);
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), ARRAY_SIZE(sent),
		      "unexpected queue occupancy after ISR puts");

	for (size_t i = 0; i < ARRAY_SIZE(sent); ++i) {
		zassert_ok(k_msgq_get(&test_msgq, &received, K_NO_WAIT),
			   "thread get %u failed", (unsigned int)i);
		zassert_mem_equal(&received, &sent[i], sizeof(received),
				  "message %u differs from ISR data", (unsigned int)i);
	}

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "queue not empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
