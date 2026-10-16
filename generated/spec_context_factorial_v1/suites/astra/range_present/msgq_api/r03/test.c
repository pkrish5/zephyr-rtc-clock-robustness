#include <zephyr/kernel.h>
#include <zephyr/irq_offload.h>
#include <zephyr/ztest.h>
#include <stdbool.h>
#include <stdint.h>

enum { MESSAGE_SIZE = 8, MESSAGE_COUNT = 2 };

K_MSGQ_DEFINE(test_queue, MESSAGE_SIZE, MESSAGE_COUNT, 1);

static const uint8_t messages[MESSAGE_COUNT][MESSAGE_SIZE] = {
	{ 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77 },
	{ 0xff, 0xee, 0xdd, 0xcc, 0xbb, 0xaa, 0x99, 0x88 },
};
static int put_results[MESSAGE_COUNT];
static bool ran_in_isr;

static void put_from_isr(const void *unused)
{
	(void)unused;
	ran_in_isr = k_is_in_isr();

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		/* ISR operations must never request a blocking timeout. */
		put_results[i] = k_msgq_put(&test_queue, messages[i], K_NO_WAIT);
	}
}

/* Run in supervisor mode so irq_offload is callable. */
ZTEST(msgq_isr, test_isr_put_thread_get)
{
	uint8_t received[MESSAGE_SIZE];

	zassert_equal(k_msgq_num_used_get(&test_queue), 0U,
		      "Queue must initially be empty");
	ran_in_isr = false;
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		put_results[i] = -1;
	}

	irq_offload(put_from_isr, NULL);

	zassert_true(ran_in_isr, "Producer must execute in interrupt context");
	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_equal(put_results[i], 0, "Nonblocking ISR put failed");
	}
	zassert_equal(k_msgq_num_used_get(&test_queue), MESSAGE_COUNT,
		      "Expected both messages to be queued");

	for (int i = 0; i < MESSAGE_COUNT; ++i) {
		zassert_ok(k_msgq_get(&test_queue, received, K_NO_WAIT),
			   "Thread retrieval failed");
		zassert_mem_equal(received, messages[i], MESSAGE_SIZE,
				  "Message bytes or FIFO order differ");
	}

	zassert_equal(k_msgq_num_used_get(&test_queue), 0U,
		      "Queue must be empty after retrieval");
}

ZTEST_SUITE(msgq_isr, NULL, NULL, NULL, NULL, NULL);
