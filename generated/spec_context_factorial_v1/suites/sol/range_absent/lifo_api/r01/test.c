#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
    void *link; /* Reserved for kernel linkage. */
    int value;
};

struct test_context {
    struct k_lifo lifo;
    struct lifo_item first;
    struct lifo_item second;
    volatile bool ran_in_isr;
};

static void put_from_isr(const void *arg)
{
    struct test_context *ctx = (struct test_context *)arg;

    ctx->ran_in_isr = k_is_in_isr();
    k_lifo_put(&ctx->lifo, &ctx->first);
    k_lifo_put(&ctx->lifo, &ctx->second);
}

ZTEST(lifo_irq, test_isr_to_thread_order)
{
    struct test_context ctx = {
        .first = { .value = 1 },
        .second = { .value = 2 },
    };

    k_lifo_init(&ctx.lifo);
    irq_offload(put_from_isr, &ctx);

    zassert_true(ctx.ran_in_isr, "offloaded handler did not run in ISR context");
    zassert_true(k_lifo_get(&ctx.lifo, K_NO_WAIT) == &ctx.second,
                 "second item was not retrieved first");
    zassert_true(k_lifo_get(&ctx.lifo, K_NO_WAIT) == &ctx.first,
                 "first item was not retrieved second");
    zassert_is_null(k_lifo_get(&ctx.lifo, K_NO_WAIT), "LIFO is not empty");
}

ZTEST_SUITE(lifo_irq, NULL, NULL, NULL, NULL, NULL);
