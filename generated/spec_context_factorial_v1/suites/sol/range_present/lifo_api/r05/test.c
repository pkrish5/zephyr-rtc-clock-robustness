#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
	void *link;
	int value;
};

struct isr_context {
	struct k_lifo *lifo;
	struct lifo_item *first;
	struct lifo_item *second;
	volatile bool ran_in_isr;
};

static void put_items_from_isr(const void *parameter)
{
	struct isr_context *ctx = (struct isr_context *)parameter;

	ctx->ran_in_isr = k_is_in_isr();
	k_lifo_put(ctx->lifo, ctx->first);
	k_lifo_put(ctx->lifo, ctx->second);
}

ZTEST(lifo_isr, test_interrupt_to_thread_order)
{
	struct k_lifo lifo;
	struct lifo_item first = { .link = NULL, .value = 1 };
	struct lifo_item second = { .link = NULL, .value = 2 };
	struct isr_context ctx = {
		.lifo = &lifo,
		.first = &first,
		.second = &second,
		.ran_in_isr = false,
	};

	k_lifo_init(&lifo);
	irq_offload(put_items_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "callback did not run in interrupt context");
	zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == &second,
		     "first get did not return the last item inserted");
	zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == &first,
		     "second get did not return the first item inserted");
	zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT), "LIFO is not empty");
}

ZTEST_SUITE(lifo_isr, NULL, NULL, NULL, NULL, NULL);
