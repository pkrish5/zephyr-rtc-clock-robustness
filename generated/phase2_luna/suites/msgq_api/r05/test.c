#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#define MSG_SIZE 4
#define MSG_COUNT 2

K_MSGQ_DEFINE(test_msgq, MSG_SIZE, MSG_COUNT, 1);

static const uint8_t sent[MSG_COUNT][MSG_SIZE] = {
    { 0x12, 0x34, 0x56, 0x78 },
    { 0x9a, 0xbc, 0xde, 0xf0 },
};
static int put_results[MSG_COUNT];
static unsigned int puts_done;

static void msgq_put_isr(const void *unused)
{
    ARG_UNUSED(unused);

    for (unsigned int i = 0; i < MSG_COUNT; ++i) {
        put_results[i] = k_msgq_put(&test_msgq, sent[i], K_NO_WAIT);
        ++puts_done;
    }
}

ZTEST(msgq_isr, test_isr_put_and_thread_get)
{
    uint8_t received[MSG_SIZE];

    k_msgq_purge(&test_msgq);
    puts_done = 0;
    irq_offload(msgq_put_isr, NULL);

    zassert_equal(puts_done, MSG_COUNT, "ISR did not attempt all puts");
    for (unsigned int i = 0; i < MSG_COUNT; ++i) {
        zassert_equal(put_results[i], 0, "ISR put %u failed", i);
    }
    zassert_equal(k_msgq_num_used_get(&test_msgq), MSG_COUNT,
                  "unexpected queue count after ISR puts");

    for (unsigned int i = 0; i < MSG_COUNT; ++i) {
        zassert_ok(k_msgq_get(&test_msgq, received, K_NO_WAIT),
                   "get %u failed", i);
        zassert_mem_equal(received, sent[i], MSG_SIZE,
                          "message %u contents differ", i);
    }
    zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
                  "queue should be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
