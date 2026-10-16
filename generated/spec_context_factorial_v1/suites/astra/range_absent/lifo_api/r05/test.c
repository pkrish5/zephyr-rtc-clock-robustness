#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct lifo_item {
	void *link; /* First word reserved for kernel linkage. */
	int value;
};

struct test_context {
	struct k_lifo lifo;
	struct lifo_item first;
	struct lifo_item second;
	bool ran_in_isr;
};

static void lifo_isr(const void *arg)
{
	struct test_context *ctx = (struct test_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_lifo_put(&ctx->lifo, &ctx->first);
	k_lifo_put(&ctx->lifo, &ctx->second);
}

ZTEST(lifo_isr_transfer, test_reverse_order)
{
	struct test_context ctx = {
		.first = { .value = 1 },
		.second = { .value = 2 },
	};

	k_lifo_init(&ctx.lifo);
	irq_offload(lifo_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "Offload handler must run in ISR context");
	zassert_equal_ptr(k_lifo_get(&ctx.lifo, K_NO_WAIT), &ctx.second,
			  "Expected the last item inserted by the ISR");
	zassert_equal_ptr(k_lifo_get(&ctx.lifo, K_NO_WAIT), &ctx.first,
			  "Expected the first item inserted by the ISR");
	zassert_is_null(k_lifo_get(&ctx.lifo, K_NO_WAIT),
			"LIFO must be empty after both items are retrieved");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
