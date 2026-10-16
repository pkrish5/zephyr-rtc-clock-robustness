"""Deliberately brittle test: a fixed virtual-time sleep before the assertion."""

FIXED_SLEEP_NS = 10_050_000
LED_BIT = 1 << 12


def run(session):
    session.run_for_ns(FIXED_SLEEP_NS)
    return bool(session.observe_gpio() & LED_BIT)
