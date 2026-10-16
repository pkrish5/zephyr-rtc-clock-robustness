#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>
#include <string.h>

struct message {
    uint8_t bytes[4];
};

K_MSGQ_DEFINE(test_msgq, sizeof(struct message), 2, 4);

static const struct message sent[] = {
    {{0x12, 0x34, 0x56, 0x78}},
    {{0xA5, 0x5A, 0x00, 0xFF}},
};

static void put_from_isr(const void *arg)
{
    int *results = (int *)arg;

    for (size_t i = 0; i < 2; ++i) {
        results[i] = k_msgq_put(&test_msgq, &sent[i], K_NO_WAIT);
    }
}

ZTEST(msgq_isr, test_put_from_isr_get_from_thread)
{
    int results[2];
    struct message received;

    zassert_equal(k_msgq_num_used_get(&test_msgq), 0U);
    irq_offload(put_from_isr, results);

    for (size_t i = 0; i < 2; ++i) {
        zassert_equal(results[i], 0, "ISR put failed");
    }
    zassert_equal(k_msgq_num_used_get(&test_msgq), 2U);

    for (size_t i = 0; i < 2; ++i) {
        zassert_equal(k_msgq_get(&test_msgq, &received, K_NO_WAIT), 0);
        zassert_equal(memcmp(&received, &sent[i], sizeof(received)), 0,
                      "retrieved message differs from ISR message");
    }

    zassert_equal(k_msgq_num_used_get(&test_msgq), 0U);
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
