#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct lifo_item {
	void *link;
	int value;
};

struct test_context {
	struct k_lifo lifo;
	struct lifo_item first;
	struct lifo_item second;
	bool isr_used;
};

static void lifo_isr(const void *arg)
{
	struct test_context *ctx = (struct test_context *)arg;

	ctx->isr_used = k_is_in_isr();
	k_lifo_put(&ctx->lifo, &ctx->first);
	k_lifo_put(&ctx->lifo, &ctx->second);
}

ZTEST(lifo_isr_transfer, test_reverse_order_and_empty)
{
	struct test_context ctx = {
		.first = { .value = 1 },
		.second = { .value = 2 },
		.isr_used = false,
	};

	k_lifo_init(&ctx.lifo);
	irq_offload(lifo_isr, &ctx);

	zassert_true(ctx.isr_used, "Handler must execute in interrupt context");
	zassert_equal_ptr(k_lifo_get(&ctx.lifo, K_NO_WAIT), &ctx.second,
			  "Last inserted item must be retrieved first");
	zassert_equal_ptr(k_lifo_get(&ctx.lifo, K_NO_WAIT), &ctx.first,
			  "First inserted item must be retrieved second");
	zassert_is_null(k_lifo_get(&ctx.lifo, K_NO_WAIT),
			"LIFO must be empty after both items are retrieved");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
