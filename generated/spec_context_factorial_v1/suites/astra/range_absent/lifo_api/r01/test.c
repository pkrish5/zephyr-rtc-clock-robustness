#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct lifo_item {
	void *link;
	int value;
};

struct transfer_context {
	struct k_lifo lifo;
	struct lifo_item first;
	struct lifo_item second;
	volatile bool ran_in_isr;
};

static void put_from_isr(const void *arg)
{
	struct transfer_context *ctx = (struct transfer_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_lifo_put(&ctx->lifo, &ctx->first);
	k_lifo_put(&ctx->lifo, &ctx->second);
}

ZTEST(lifo_isr, test_isr_to_thread_transfer)
{
	struct transfer_context ctx = {
		.first = { .value = 1 },
		.second = { .value = 2 },
	};
	void *first_get;
	void *second_get;

	k_lifo_init(&ctx.lifo);
	irq_offload(put_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "Producer did not run in ISR context");
	zassert_false(k_is_in_isr(), "Consumer must run in thread context");

	first_get = k_lifo_get(&ctx.lifo, K_NO_WAIT);
	second_get = k_lifo_get(&ctx.lifo, K_NO_WAIT);

	zassert_equal_ptr(first_get, &ctx.second,
			 "First get must return the last inserted item");
	zassert_equal_ptr(second_get, &ctx.first,
			 "Second get must return the first inserted item");
	zassert_is_null(k_lifo_get(&ctx.lifo, K_NO_WAIT),
			"LIFO must be empty after both gets");
}

ZTEST_SUITE(lifo_isr, NULL, NULL, NULL, NULL, NULL);
