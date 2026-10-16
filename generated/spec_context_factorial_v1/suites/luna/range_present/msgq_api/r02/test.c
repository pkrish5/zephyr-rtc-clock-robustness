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
static volatile int isr_put_status[MSG_COUNT];

static void msgq_put_isr(const void *arg)
{
    ARG_UNUSED(arg);

    for (int i = 0; i < MSG_COUNT; ++i) {
        isr_put_status[i] = k_msgq_put(&test_msgq, sent[i], K_NO_WAIT);
    }
}

ZTEST(msgq_isr, test_isr_put_and_thread_get)
{
    uint8_t received[MSG_SIZE];

    k_msgq_purge(&test_msgq);
    isr_put_status[0] = -1;
    isr_put_status[1] = -1;

    irq_offload(msgq_put_isr, NULL);

    zassert_equal(isr_put_status[0], 0, "first ISR put failed");
    zassert_equal(isr_put_status[1], 0, "second ISR put failed");
    zassert_equal(k_msgq_num_used_get(&test_msgq), MSG_COUNT,
                  "unexpected queue count after ISR puts");

    for (int i = 0; i < MSG_COUNT; ++i) {
        zassert_equal(k_msgq_get(&test_msgq, received, K_NO_WAIT), 0,
                      "message retrieval failed");
        zassert_mem_equal(received, sent[i], MSG_SIZE,
                         "retrieved message differs from ISR data");
    }

    zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
                  "queue should be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
