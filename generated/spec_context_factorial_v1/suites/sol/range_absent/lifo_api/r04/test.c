#include <stdbool.h>
#include <stddef.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
	void *link; /* Reserved for kernel linkage. */
	int value;
};

struct offload_context {
	struct k_lifo *lifo;
	struct lifo_item *first;
	struct lifo_item *second;
	bool ran_in_isr;
};

static void put_from_isr(const void *arg)
{
	struct offload_context *ctx = (struct offload_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_lifo_put(ctx->lifo, ctx->first);
	k_lifo_put(ctx->lifo, ctx->second);
}

ZTEST(lifo_irq, test_isr_to_thread_order)
{
	struct k_lifo lifo;
	struct lifo_item first = { .link = NULL, .value = 1 };
	struct lifo_item second = { .link = NULL, .value = 2 };
	struct offload_context ctx = {
		.lifo = &lifo,
		.first = &first,
		.second = &second,
		.ran_in_isr = false,
	};

	k_lifo_init(&lifo);
	irq_offload(put_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "offload did not run in interrupt context");
	zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == &second,
		     "first get did not return the last item put");
	zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == &first,
		     "second get did not return the first item put");
	zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT), "LIFO is not empty");
}

ZTEST_SUITE(lifo_irq, NULL, NULL, NULL, NULL, NULL);
