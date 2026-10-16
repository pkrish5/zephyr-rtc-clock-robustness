#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

K_MSGQ_DEFINE(isr_msgq, 4, 2, 4);

struct offload_context {
    uint8_t messages[2][4];
    int put_result[2];
};

static void put_from_isr(const void *arg)
{
    struct offload_context *ctx = (struct offload_context *)arg;

    ctx->put_result[0] = k_msgq_put(&isr_msgq, ctx->messages[0], K_NO_WAIT);
    ctx->put_result[1] = k_msgq_put(&isr_msgq, ctx->messages[1], K_NO_WAIT);
}

ZTEST(msgq_isr_thread, test_isr_put_thread_get)
{
    struct offload_context ctx = {
        .messages = {{0x12, 0x34, 0x56, 0x78}, {0x9a, 0xbc, 0xde, 0xf0}},
        .put_result = {-1, -1},
    };
    uint8_t received[4];

    zassert_equal(k_msgq_num_used_get(&isr_msgq), 0);
    irq_offload(put_from_isr, &ctx);

    zassert_equal(ctx.put_result[0], 0);
    zassert_equal(ctx.put_result[1], 0);
    zassert_equal(k_msgq_num_used_get(&isr_msgq), 2);

    for (int message = 0; message < 2; ++message) {
        zassert_equal(k_msgq_get(&isr_msgq, received, K_NO_WAIT), 0);
        for (int byte = 0; byte < 4; ++byte) {
            zassert_equal(received[byte], ctx.messages[message][byte]);
        }
    }

    zassert_equal(k_msgq_num_used_get(&isr_msgq), 0);
}

ZTEST_SUITE(msgq_isr_thread, NULL, NULL, NULL, NULL, NULL);
