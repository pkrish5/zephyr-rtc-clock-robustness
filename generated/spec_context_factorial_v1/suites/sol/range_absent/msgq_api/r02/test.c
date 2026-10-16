#include <stdint.h>
#include <zephyr/irq_offload.h>
#include <zephyr/kernel.h>
#include <zephyr/ztest.h>

struct message {
	uint8_t bytes[4];
};

K_MSGQ_DEFINE(test_msgq, sizeof(struct message), 2, 4);

struct isr_context {
	struct message sent[2];
	int put_result[2];
};

static void put_from_isr(const void *arg)
{
	struct isr_context *ctx = (struct isr_context *)arg;

	ctx->put_result[0] = k_msgq_put(&test_msgq, &ctx->sent[0], K_NO_WAIT);
	ctx->put_result[1] = k_msgq_put(&test_msgq, &ctx->sent[1], K_NO_WAIT);
}

ZTEST(msgq_isr, test_put_from_isr_and_get_from_thread)
{
	struct isr_context ctx = {
		.sent = {
			{ .bytes = { 0x12, 0x34, 0x56, 0x78 } },
			{ .bytes = { 0x9a, 0xbc, 0xde, 0xf0 } },
		},
	};
	struct message received;

	k_msgq_purge(&test_msgq);
	irq_offload(put_from_isr, &ctx);

	zassert_equal(ctx.put_result[0], 0, "first ISR put failed");
	zassert_equal(ctx.put_result[1], 0, "second ISR put failed");
	zassert_equal(k_msgq_num_used_get(&test_msgq), 2, "queue should contain two messages");

	zassert_equal(k_msgq_get(&test_msgq, &received, K_NO_WAIT), 0, "first get failed");
	zassert_mem_equal(&received, &ctx.sent[0], sizeof(received), "first message differs");
	zassert_equal(k_msgq_get(&test_msgq, &received, K_NO_WAIT), 0, "second get failed");
	zassert_mem_equal(&received, &ctx.sent[1], sizeof(received), "second message differs");
	zassert_equal(k_msgq_num_used_get(&test_msgq), 0, "queue is not empty");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
