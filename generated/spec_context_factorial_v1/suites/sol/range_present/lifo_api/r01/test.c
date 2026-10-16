#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
	void *link; /* Reserved for kernel linkage. */
	int value;
};

struct test_context {
	struct k_lifo lifo;
	struct lifo_item items[2];
	bool ran_in_isr;
};

static void put_from_isr(const void *arg)
{
	struct test_context *ctx = (struct test_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_lifo_put(&ctx->lifo, &ctx->items[0]);
	k_lifo_put(&ctx->lifo, &ctx->items[1]);
}

ZTEST(lifo_irq, test_isr_to_thread_order)
{
	struct test_context ctx = {
		.items = {{.value = 1}, {.value = 2}},
	};

	k_lifo_init(&ctx.lifo);
	irq_offload(put_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "producer did not run in ISR context");
	zassert_true(k_lifo_get(&ctx.lifo, K_NO_WAIT) == &ctx.items[1],
		     "first get did not return the last item put");
	zassert_true(k_lifo_get(&ctx.lifo, K_NO_WAIT) == &ctx.items[0],
		     "second get did not return the first item put");
	zassert_is_null(k_lifo_get(&ctx.lifo, K_NO_WAIT),
			"LIFO was not empty after two gets");
}

ZTEST_SUITE(lifo_irq, NULL, NULL, NULL, NULL, NULL);