#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>

#include <stdint.h>

#define MSG_SIZE 4
#define MSG_COUNT 2

K_MSGQ_DEFINE(test_msgq, MSG_SIZE, MSG_COUNT, 4);

static const uint8_t messages[MSG_COUNT][MSG_SIZE] = {
    {0x12, 0x34, 0x56, 0x78},
    {0xA5, 0x5A, 0xC3, 0x3C},
};

struct isr_results {
    bool ran_in_isr;
    int put_status[MSG_COUNT];
};

static void put_messages_from_isr(const void *arg)
{
    struct isr_results *results = (struct isr_results *)arg;

    results->ran_in_isr = k_is_in_isr();
    for (int i = 0; i < MSG_COUNT; i++) {
        results->put_status[i] = k_msgq_put(&test_msgq, messages[i], K_NO_WAIT);
    }
}

ZTEST(msgq_isr, test_put_from_isr_get_from_thread)
{
    struct isr_results results = {0};
    uint8_t received[MSG_SIZE];

    k_msgq_purge(&test_msgq);
    irq_offload(put_messages_from_isr, &results);

    zassert_true(results.ran_in_isr);
    for (int i = 0; i < MSG_COUNT; i++) {
        zassert_equal(results.put_status[i], 0);
    }
    zassert_equal(k_msgq_num_used_get(&test_msgq), MSG_COUNT);

    for (int i = 0; i < MSG_COUNT; i++) {
        zassert_equal(k_msgq_get(&test_msgq, received, K_NO_WAIT), 0);
        zassert_mem_equal(received, messages[i], MSG_SIZE);
    }

    zassert_equal(k_msgq_num_used_get(&test_msgq), 0);
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
