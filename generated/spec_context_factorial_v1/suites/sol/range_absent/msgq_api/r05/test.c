#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <string.h>

K_MSGQ_DEFINE(test_msgq, 4, 2, 1);

static const uint8_t sent[2][4] = {
    {0x12, 0x34, 0x56, 0x78},
    {0x9a, 0xbc, 0xde, 0xf0},
};
static int put_result[2];
static bool ran_in_isr;

static void put_from_isr(const void *arg)
{
    ARG_UNUSED(arg);

    ran_in_isr = k_is_in_isr();
    put_result[0] = k_msgq_put(&test_msgq, sent[0], K_NO_WAIT);
    put_result[1] = k_msgq_put(&test_msgq, sent[1], K_NO_WAIT);
}

ZTEST(msgq_isr, test_put_in_isr_get_in_thread)
{
    uint8_t received[4];

    k_msgq_purge(&test_msgq);
    ran_in_isr = false;
    put_result[0] = -1;
    put_result[1] = -1;

    irq_offload(put_from_isr, NULL);

    zassert_true(ran_in_isr, "callback did not run in ISR context");
    zassert_equal(put_result[0], 0, "first ISR put failed");
    zassert_equal(put_result[1], 0, "second ISR put failed");
    zassert_equal(k_msgq_num_used_get(&test_msgq), 2, "queue count after puts");

    zassert_equal(k_msgq_get(&test_msgq, received, K_NO_WAIT), 0,
                  "first get failed");
    zassert_equal(memcmp(received, sent[0], sizeof(received)), 0,
                  "first message differs");

    zassert_equal(k_msgq_get(&test_msgq, received, K_NO_WAIT), 0,
                  "second get failed");
    zassert_equal(memcmp(received, sent[1], sizeof(received)), 0,
                  "second message differs");
    zassert_equal(k_msgq_num_used_get(&test_msgq), 0, "queue is not empty");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
