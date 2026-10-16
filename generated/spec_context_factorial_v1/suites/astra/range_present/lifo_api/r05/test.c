#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>

struct lifo_item {
	void *link; /* First word reserved for kernel linkage. */
	int value;
};

struct isr_context {
	struct k_lifo *lifo;
	struct lifo_item *first;
	struct lifo_item *second;
	bool ran_in_isr;
};

static void put_from_isr(const void *arg)
{
	struct isr_context *ctx = (struct isr_context *)arg;

	ctx->ran_in_isr = k_is_in_isr();
	k_lifo_put(ctx->lifo, ctx->first);
	k_lifo_put(ctx->lifo, ctx->second);
}

ZTEST(lifo_isr, test_transfer_to_thread)
{
	struct k_lifo lifo;
	struct lifo_item first = { .value = 1 };
	struct lifo_item second = { .value = 2 };
	struct isr_context ctx = {
		.lifo = &lifo,
		.first = &first,
		.second = &second,
		.ran_in_isr = false,
	};

	k_lifo_init(&lifo);
	zassert_false(k_is_in_isr(), "Receiver must run in thread context");

	/* Offload completes before retrieval; no timing bound is assumed. */
	irq_offload(put_from_isr, &ctx);

	zassert_true(ctx.ran_in_isr, "Producer did not run in ISR context");
	zassert_equal_ptr(k_lifo_get(&lifo, K_NO_WAIT), &second,
			  "Last inserted item must be retrieved first");
	zassert_equal_ptr(k_lifo_get(&lifo, K_NO_WAIT), &first,
			  "First inserted item must be retrieved second");
	zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT),
			"LIFO must be empty after both gets");
}

ZTEST_SUITE(lifo_isr, NULL, NULL, NULL, NULL, NULL);
