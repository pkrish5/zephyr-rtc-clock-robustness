#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>
#include <stddef.h>

#define MSG_SIZE 4
#define MSG_COUNT 2

K_MSGQ_DEFINE(test_msgq, MSG_SIZE, MSG_COUNT, 4);

static const uint8_t messages[MSG_COUNT][MSG_SIZE] = {
    {0x12, 0x34, 0x56, 0x78},
    {0x9a, 0xbc, 0xde, 0xf0},
};
static int put_result[MSG_COUNT];

static void put_from_isr(const void *arg)
{
    (void)arg;

    for (int i = 0; i < MSG_COUNT; i++) {
        put_result[i] = k_msgq_put(&test_msgq, messages[i], K_NO_WAIT);
    }
}

ZTEST(msgq_isr, test_messages_from_isr)
{
    uint8_t received[MSG_SIZE];

    zassert_equal(k_msgq_num_used_get(&test_msgq), 0, "queue not initially empty");
    irq_offload(put_from_isr, NULL);

    for (int i = 0; i < MSG_COUNT; i++) {
        zassert_equal(put_result[i], 0, "ISR put failed");
    }
    zassert_equal(k_msgq_num_used_get(&test_msgq), MSG_COUNT, "wrong queue count");

    for (int i = 0; i < MSG_COUNT; i++) {
        zassert_equal(k_msgq_get(&test_msgq, received, K_NO_WAIT), 0,
                      "message retrieval failed");
        for (int j = 0; j < MSG_SIZE; j++) {
            zassert_equal(received[j], messages[i][j], "message byte mismatch");
        }
    }

    zassert_equal(k_msgq_num_used_get(&test_msgq), 0, "queue not empty");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
