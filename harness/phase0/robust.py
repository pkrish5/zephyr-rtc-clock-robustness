"""Event wait: poll the observable GPIO output, with a finite deadline."""

POLL_NS = 1_000_000
DEADLINE_NS = 12_000_000
LED_BIT = 1 << 12


def run(session):
    if session.observe_gpio() & LED_BIT:
        return True
    while session.elapsed_ns < DEADLINE_NS:
        session.run_for_ns(POLL_NS)
        if session.observe_gpio() & LED_BIT:
            return True
    return False
