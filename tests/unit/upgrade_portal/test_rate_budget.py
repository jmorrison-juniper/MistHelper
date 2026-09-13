"""Prove that one upgrade run takes no more than 7.2 percent of the hourly API quota.

Why:
    Task T220 asks for a guard on the promise the portal makes to the operator:
    an upgrade run leaves almost all of the Mist API quota for the rest of
    MistHelper. Four separate constants carry the parts of that promise, and two
    of them live in different packages. A change to any one of them moves the
    percentage without any other test noticing, because no existing test ties
    the whole chain to the 7.2 percent figure.

    This file counts calls instead of measuring elapsed seconds. A wall-clock
    assertion fails at random on a loaded developer machine or a slow build
    agent, and a test that fails at random gets ignored. A call count is exact
    on every machine.

    The counted chain, all values read from the source:

    1. `phase_gate.PHASE_DEADLINE_SECONDS` is 1800 seconds for one phase.
    2. `gate.POLL_INTERVAL_SECONDS` is 20 seconds, so a phase holds 90 rounds.
    3. `phase_gate.CALLS_PER_ROUND` is 2, so a phase costs 180 calls.
    4. One device family polls at a time. The event stream and the statistics
       stream each cost 180 calls an hour, so the pair costs 360 calls an hour.
    5. `gate.HOURLY_CALL_QUOTA` is 5000, which mirrors the shared limiter
       default `_DEFAULT_REQUEST_LIMIT` in `src/utils/rate_limiting.py`.
    6. 360 of 5000 is 7.2 percent.

    Every assertion below uses whole numbers. The direct float expression
    `360 / 5000 * 100` gives 7.199999999999999, so a float comparison would need
    a tolerance that hides real drift.
"""

from __future__ import annotations  # Keeps every annotation as text, per the repository style.

from src.upgrade_portal.upgrade import gate, phase_gate  # The two modules that hold the budget constants.
from src.utils import rate_limiting  # The shared limiter that owns the real hourly quota.

BUDGET_PARTS_PER_THOUSAND = 72  # 7.2 percent written as a whole number of parts per thousand.
PARTS_PER_THOUSAND = 1000  # The scale that turns the percentage into exact integer arithmetic.
EXPECTED_ROUNDS_PER_PHASE = 90  # 1800 seconds of deadline divided by a 20 second poll interval.
EXPECTED_CALLS_PER_PHASE = 180  # 90 rounds at 2 calls a round.
POLL_STREAMS = 2  # One event stream and one statistics stream run together.
EXPECTED_CALLS_PER_HOUR = 360  # 180 calls a stream an hour, for two streams.


def test_the_phase_deadline_and_the_poll_interval_give_ninety_rounds() -> None:
    """The 1800 second phase deadline at a 20 second interval gives 90 poll rounds.

    Why:
        This is the first link of the budget chain. A shorter interval or a
        longer deadline raises the round count, and every later number grows
        with it. The test reads both constants from the source, so a change to
        either one fails here first and names the cause.
    """
    rounds = phase_gate.PHASE_DEADLINE_SECONDS // gate.POLL_INTERVAL_SECONDS  # The derivation, from source constants.
    assert phase_gate.PHASE_DEADLINE_SECONDS == 1800  # The deadline the phase gate publishes.
    assert gate.POLL_INTERVAL_SECONDS == 20  # The interval the settle gate publishes.
    assert rounds == EXPECTED_ROUNDS_PER_PHASE  # The derived count matches the documented count.
    assert phase_gate.polls_per_phase() == EXPECTED_ROUNDS_PER_PHASE  # The helper agrees with the raw arithmetic.


def test_one_phase_costs_one_hundred_and_eighty_cloud_calls() -> None:
    """A phase that runs to its deadline costs 180 cloud calls.

    Why:
        Each poll round costs a fixed pair of calls, whatever the size of the
        fleet. That fixed cost is what keeps a large site inside the same
        budget as a small one. A per-device call would break the promise, so
        the round cost is pinned here.
    """
    assert phase_gate.CALLS_PER_ROUND == POLL_STREAMS  # Two calls a round, one for each stream.
    calls = EXPECTED_ROUNDS_PER_PHASE * phase_gate.CALLS_PER_ROUND  # The derivation, from source constants.
    assert calls == EXPECTED_CALLS_PER_PHASE  # The derived cost matches the documented cost.
    assert phase_gate.calls_per_phase() == EXPECTED_CALLS_PER_PHASE  # The helper agrees with the raw arithmetic.
    assert phase_gate.calls_per_phase() > 0  # The run does real work, so the budget measures something.


def test_two_poll_streams_reach_three_hundred_and_sixty_calls_an_hour() -> None:
    """One event stream and one statistics stream cost 360 calls an hour together.

    Why:
        Only one device family polls at a time, so the hourly cost is the pair
        of streams and not the number of families. This test states that rule
        as arithmetic. If a third stream ever joins, the count moves to 540 and
        the test fails with the reason in view.
    """
    per_stream = gate.polls_per_hour(gate.POLL_INTERVAL_SECONDS)  # Poll rounds an hour for one stream.
    assert per_stream == EXPECTED_CALLS_PER_PHASE  # 3600 seconds divided by a 20 second interval.
    assert per_stream * POLL_STREAMS == EXPECTED_CALLS_PER_HOUR  # The two streams together.
    assert gate.MAX_CALLS_PER_HOUR == EXPECTED_CALLS_PER_HOUR  # The published ceiling matches the derivation.


def test_the_phase_cost_scales_to_the_same_hourly_figure() -> None:
    """The 180 calls of a 1800 second phase scale to 360 calls an hour.

    Why:
        The phase gate counts calls over a 1800 second phase and the settle
        gate counts them over an hour. The two modules must describe the same
        rate, or one of them is wrong. This test converts the phase figure to
        an hourly figure and compares it with the published ceiling.
    """
    hourly = phase_gate.calls_per_phase() * gate.SECONDS_PER_HOUR // phase_gate.PHASE_DEADLINE_SECONDS  # Rate change.
    assert gate.SECONDS_PER_HOUR == 3600  # The hour the settle gate counts against.
    assert hourly == EXPECTED_CALLS_PER_HOUR  # The two modules describe one rate.
    assert hourly == gate.MAX_CALLS_PER_HOUR  # The rate matches the published ceiling.


def test_the_portal_quota_matches_the_shared_rate_limiter() -> None:
    """The portal hourly quota matches the shared limiter default of 5000 calls.

    Why:
        `gate.HOURLY_CALL_QUOTA` is a copy of the limiter default that lives in
        another package. A copy drifts silently. This test binds the copy to the
        original, so a change to the shared limiter fails the portal budget test
        instead of quietly making the published percentage wrong.
    """
    shared_default = rate_limiting._DEFAULT_REQUEST_LIMIT  # The private name is the only copy of the real quota.
    assert gate.HOURLY_CALL_QUOTA == shared_default  # The portal copy tracks the shared limiter.
    assert gate.HOURLY_CALL_QUOTA == 5000  # The value both modules agree on today.


def test_one_upgrade_run_takes_at_most_7_2_percent_of_the_hourly_quota() -> None:
    """One upgrade run takes 7.2 percent of the hourly quota, and no more.

    Why:
        This is the claim of task T220 and the headline promise of the feature.
        The comparison uses parts per thousand rather than a percentage float,
        because `360 / 5000 * 100` gives 7.199999999999999 and any float
        tolerance wide enough to accept that value also accepts real drift.
    """
    used = gate.MAX_CALLS_PER_HOUR * PARTS_PER_THOUSAND  # The run cost, scaled to parts per thousand.
    budget = BUDGET_PARTS_PER_THOUSAND * gate.HOURLY_CALL_QUOTA  # The 7.2 percent budget, at the same scale.
    assert used <= budget  # The run never takes more than the documented share.
    assert used == budget  # The run takes exactly the documented share today.
    assert gate.HOURLY_CALL_QUOTA - gate.MAX_CALLS_PER_HOUR == 4640  # The quota left for the rest of MistHelper.


def test_the_whole_chain_derives_the_budget_from_the_two_source_constants() -> None:
    """The deadline and the poll interval alone derive the 7.2 percent figure.

    Why:
        The tests above each check one link. This one walks the whole chain from
        the two constants an engineer is most likely to change, so a reader sees
        the full derivation in one place and a tuning change fails one obvious
        test instead of several partial ones.
    """
    rounds = phase_gate.PHASE_DEADLINE_SECONDS // gate.POLL_INTERVAL_SECONDS  # Step 1: rounds in one phase.
    phase_calls = rounds * phase_gate.CALLS_PER_ROUND  # Step 2: calls in one phase.
    hourly = phase_calls * gate.SECONDS_PER_HOUR // phase_gate.PHASE_DEADLINE_SECONDS  # Step 3: calls in one hour.
    assert (rounds, phase_calls, hourly) == (90, 180, 360)  # The chain lands on the documented numbers.
    assert hourly * PARTS_PER_THOUSAND == BUDGET_PARTS_PER_THOUSAND * gate.HOURLY_CALL_QUOTA  # Step 4: 7.2 percent.


def test_a_slower_poll_interval_costs_less_quota() -> None:
    """Doubling the poll interval halves the hourly call cost.

    Why:
        The budget must react to the interval, or the arithmetic above only
        looks correct for one hard-coded pair of numbers. A second interval
        proves the helper divides rather than returns a constant, which is the
        way a budget test most often becomes vacuous.
    """
    slower = gate.polls_per_hour(gate.POLL_INTERVAL_SECONDS * 2)  # A 40 second interval.
    faster = gate.polls_per_hour(gate.POLL_INTERVAL_SECONDS)  # The 20 second interval in use.
    assert slower * 2 == faster  # Half the rate for twice the interval.
    assert slower > 0  # The slower interval still does real work.
