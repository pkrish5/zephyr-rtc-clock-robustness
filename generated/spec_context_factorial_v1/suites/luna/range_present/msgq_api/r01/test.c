#include <zephyr/kernel.h>
#include <zephyr/ztest.h>
#include <string.h>

struct message {
    uint32_t sequence;
    uint8_t payload[4];
};

K_MSGQ_DEFINE(test_msgq, sizeof(struct message), 2, 4);

static const struct message sent[] = {
    { .sequence = 0x12345678, .payload = { 0x10, 0x20, 0x30, 0x40 } },
    { .sequence = 0x87654321, .payload = { 0xA1, 0xB2, 0xC3, 0xD4 } },
};
static volatile int put_result[ARRAY_SIZE(sent)];

static void put_messages_from_isr(const void *unused)
{
    ARG_UNUSED(unused);

    for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
        put_result[i] = k_msgq_put(&test_msgq, &sent[i], K_NO_WAIT);
    }
}

ZTEST(msgq_isr, test_isr_put_and_thread_get)
{
    struct message received;

    k_msgq_purge(&test_msgq);
    for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
        put_result[i] = -1;
    }

    irq_offload(put_messages_from_isr, NULL);

    for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
        zassert_equal(put_result[i], 0, "ISR put %u failed: %d", (unsigned int)i,
                      put_result[i]);
    }
    zassert_equal(k_msgq_num_used_get(&test_msgq), ARRAY_SIZE(sent),
                  "unexpected queue occupancy after ISR puts");

    for (size_t i = 0; i < ARRAY_SIZE(sent); i++) {
        zassert_ok(k_msgq_get(&test_msgq, &received, K_NO_WAIT),
                   "thread get %u failed", (unsigned int)i);
        zassert_true(memcmp(&received, &sent[i], sizeof(received)) == 0,
                     "message %u bytes differ", (unsigned int)i);
    }

    zassert_equal(k_msgq_num_used_get(&test_msgq), 0,
                  "queue not empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
