#include <stdbool.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

struct lifo_item {
    void *link; /* Reserved for kernel linkage. */
    int value;
};

struct test_context {
    struct k_lifo *lifo;
    struct lifo_item *first;
    struct lifo_item *second;
    bool ran_in_isr;
};

static void put_from_isr(const void *parameter)
{
    struct test_context *ctx = (struct test_context *)parameter;

    ctx->ran_in_isr = k_is_in_isr();
    k_lifo_put(ctx->lifo, ctx->first);
    k_lifo_put(ctx->lifo, ctx->second);
}

ZTEST(lifo_isr, transfers_in_reverse_order)
{
    struct k_lifo lifo;
    struct lifo_item first = { .value = 1 };
    struct lifo_item second = { .value = 2 };
    struct test_context ctx = {
        .lifo = &lifo,
        .first = &first,
        .second = &second,
        .ran_in_isr = false,
    };

    k_lifo_init(&lifo);
    irq_offload(put_from_isr, &ctx);

    zassert_true(ctx.ran_in_isr, "offload did not run in ISR context");
    zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == &second,
                 "first get did not return the second item");
    zassert_true(k_lifo_get(&lifo, K_NO_WAIT) == &first,
                 "second get did not return the first item");
    zassert_is_null(k_lifo_get(&lifo, K_NO_WAIT), "LIFO is not empty");
}

ZTEST_SUITE(lifo_isr, NULL, NULL, NULL, NULL, NULL);
