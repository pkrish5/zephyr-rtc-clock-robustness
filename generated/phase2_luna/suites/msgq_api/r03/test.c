#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct msgq_item {
	uint32_t id;
	uint8_t payload[4];
};

K_MSGQ_DEFINE(test_msgq, sizeof(struct msgq_item), 2, 4);

static const struct msgq_item sent[] = {
	{ .id = 0x12345678U, .payload = { 0x11, 0x22, 0x33, 0x44 } },
	{ .id = 0x89abcdefU, .payload = { 0xaa, 0xbb, 0xcc, 0xdd } },
};
static int isr_put_results[ARRAY_SIZE(sent)];

static void msgq_put_from_isr(const void *unused)
{
	ARG_UNUSED(unused);

	for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
		isr_put_results[i] = k_msgq_put(&test_msgq, &sent[i], K_NO_WAIT);
	}
}

ZTEST(msgq_isr, test_put_from_isr_and_get_in_thread)
{
	struct msgq_item received;

	k_msgq_purge(&test_msgq);
	for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
		isr_put_results[i] = -1;
	}

	irq_offload(msgq_put_from_isr, NULL);

	for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
		zassert_equal(isr_put_results[i], 0, "ISR put %zu failed: %d", i,
			      isr_put_results[i]);
	}
	zassert_equal(k_msgq_num_used_get(&test_msgq), ARRAY_SIZE(sent),
		      "unexpected queue occupancy after ISR puts");

	for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
		zassert_equal(k_msgq_get(&test_msgq, &received, K_NO_WAIT), 0,
			      "get %zu failed", i);
		zassert_mem_equal(&received, &sent[i], sizeof(received),
				  "message %zu differs from ISR data", i);
	}

	zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
		      "queue not empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
