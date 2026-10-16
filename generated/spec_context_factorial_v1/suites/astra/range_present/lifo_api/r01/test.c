#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct lifo_item {
	void *link; /* First word reserved for kernel linkage. */
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

ZTEST(lifo_isr_transfer, test_reverse_order_and_empty)
{
	struct test_context ctx = {0};
	void *first_received;
	void *second_received;

	k_lifo_init(&ctx.lifo);
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");

	/* irq_offload completes the ISR before returning. No timing bound is assumed. */
	irq_offload(lifo_isr, &ctx);
	zassert_true(ctx.ran_in_isr, "Producer did not execute in ISR context");

	first_received = k_lifo_get(&ctx.lifo, K_NO_WAIT);
	second_received = k_lifo_get(&ctx.lifo, K_NO_WAIT);

	zassert_true(first_received == &ctx.second,
		     "First get must return the last item inserted");
	zassert_true(second_received == &ctx.first,
		     "Second get must return the first item inserted");
	zassert_is_null(k_lifo_get(&ctx.lifo, K_NO_WAIT),
			"LIFO must be empty after both gets");
}

ZTEST_SUITE(lifo_isr_transfer, NULL, NULL, NULL, NULL, NULL);
