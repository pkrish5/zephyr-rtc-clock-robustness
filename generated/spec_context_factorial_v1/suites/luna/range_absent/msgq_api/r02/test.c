#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct msg {
	uint32_t id;
	uint8_t payload[4];
};

K_MSGQ_DEFINE(test_msgq, sizeof(struct msg), 2, 4);

static const struct msg sent[] = {
	{ .id = 0x12345678, .payload = { 0x10, 0x20, 0x30, 0x40 } },
	{ .id = 0xabcdef01, .payload = { 0x55, 0xaa, 0x5a, 0xa5 } },
};
static volatile int put_results[ARRAY_SIZE(sent)];

static void msgq_put_isr(const void *unused)
{
	ARG_UNUSED(unused);
	for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
		put_results[i] = k_msgq_put(&test_msgq, &sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_isr_put_and_thread_get)
{
	struct msg received;

	k_msgq_purge(&test_msgq);
	for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
		put_results[i] = -1;
	}

	irq_offload(msgq_put_isr, NULL);

	for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
		zassert_equal(put_results[i], 0, "ISR put %zu failed: %d", i,
			      put_results[i]);
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), ARRAY_SIZE(sent),
		      "unexpected queue occupancy after ISR puts");

	for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
		zassert_equal(k_msgq_get(&test_msgq, &received, K_NO_WAIT), 0,
			      "get %zu failed", i);
		zassert_mem_equal(&received, &sent[i], sizeof(received),
				  "message %zu differs", i);
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "queue should be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
