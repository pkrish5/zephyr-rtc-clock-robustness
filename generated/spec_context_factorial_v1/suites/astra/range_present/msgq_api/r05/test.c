#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdint.h>

#define MESSAGE_SIZE 8
#define MESSAGE_COUNT 2

K_MSGQ_DEFINE(test_queue, MESSAGE_SIZE, MESSAGE_COUNT, 4);

static const uint8_t messages[MESSAGE_COUNT][MESSAGE_SIZE] = {
	{ 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77 },
	{ 0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88 }
};

static int put_results[MESSAGE_COUNT];
static bool ran_in_isr;

static void put_from_isr(const void *unused)
{
	(void)unused;
	ran_in_isr = k_is_in_isr();
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		put_results[i] = k_msgq_put(&test_queue, messages[i], K_NO_WAIT);
	}
}

/* ZTEST runs in supervisor mode, including with CONFIG_TEST_USERSPACE=y. */
ZTEST(msgq_isr, test_isr_to_thread_messages)
{
	uint8_t received[MESSAGE_SIZE];

	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "Queue must start empty");
	ran_in_isr = false;
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		put_results[i] = -1;
	}

	/* irq_offload returns after the callback completes. No timing bound
	 * is inferred from the HSI frequency tolerance.
	 */
	irq_offload(put_from_isr, NULL);

	zassert_true(ran_in_isr, "Callback must execute in ISR context");
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(put_results[i], 0, "Nonblocking ISR put failed");
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), MESSAGE_COUNT,
		      "Unexpected queued message count");

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(k_msgq_get(&test_queue, received, K_NO_WAIT), 0,
			      "Thread get failed");
		zassert_mem_equal(received, messages[i], MESSAGE_SIZE,
				  "Message bytes or FIFO order differ");
		zassert_equal(k_msgq_num_used_get(&test_queue),
			      MESSAGE_COUNT - i - 1,
			      "Unexpected remaining message count");
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), 0,
		      "Queue must be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
