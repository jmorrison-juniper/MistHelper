"""Unit tests for the signal scorer (T035, FR-023, FR-023b, FR-025a)."""

from __future__ import annotations

from src.juniper_docs.classify.signal_scorer import SignalScorer


def test_scores_three_groups_and_builds_the_label() -> None:
    """The scorer builds the product, task, and domain label from the sample."""
    text = "SRX SRX configuration configure security security firewall routing"  # Sample.
    result = SignalScorer().score(text)  # Score the sample with the default threshold.
    assert result.sub_category == "srx__configuration__security"  # The joined label.
    assert result.is_fallback is False  # Strong evidence is not a fallback.
    assert result.scores  # The numeric scores are recorded.


def test_below_threshold_returns_the_fallback() -> None:
    """Weak evidence returns the fixed fallback label and empty scores."""
    result = SignalScorer(threshold=100.0).score("srx configuration security")  # High bar.
    assert result.sub_category == "unclassified-content"  # The fixed fallback label.
    assert result.is_fallback is True  # The result is a fallback.
    assert result.scores == {}  # A fallback carries no scores.


def test_empty_text_returns_the_fallback() -> None:
    """An empty sample returns the fallback label without a crash."""
    result = SignalScorer().score("")  # Score an empty sample.
    assert result.sub_category == "unclassified-content"  # The fixed fallback label.
    assert result.is_fallback is True  # An empty sample is a fallback.


def test_label_omits_a_group_with_no_signal() -> None:
    """A group with no signal above zero is omitted from the label."""
    result = SignalScorer(threshold=1.0).score("srx srx srx")  # Only a product signal.
    assert result.sub_category == "srx"  # The label carries only the product segment.
    assert result.is_fallback is False  # A single strong group is not a fallback.


def test_scoring_is_reproducible() -> None:
    """The same sample yields the same label on every run."""
    text = "mx mx monitoring monitor telemetry telemetry"  # A monitoring telemetry sample.
    first = SignalScorer().score(text)  # Score the sample once.
    second = SignalScorer().score(text)  # Score the same sample again.
    assert first.sub_category == second.sub_category  # The label is reproducible.


def test_file_name_outweighs_the_body_product() -> None:
    """A product in the file name wins over a more frequent body product (Defect A)."""
    text = "mist mist mist mist configuration security"  # Body favors the mist product.
    result = SignalScorer().score(text, "jvd-wan-edge-for-srx.pdf")  # Name names the SRX.
    assert result.sub_category.startswith("srx__")  # The file name decides the product.
    assert "srx" in result.detected_signals  # The SRX signal is recorded.


def test_word_boundary_blocks_a_substring_product() -> None:
    """A short token does not match inside a longer, unrelated word (Defect A)."""
    inside = SignalScorer().score("mistral mistral configuration security firewall")  # No mist.
    whole = SignalScorer().score("mist mist configuration security firewall")  # A real mist.
    assert "mist" not in inside.sub_category  # The substring in mistral does not match.
    assert whole.sub_category.startswith("mist__")  # The standalone mist token matches.


def test_task_segment_drops_without_a_clear_lead() -> None:
    """The task segment drops when no task type leads by the margin (Defect B)."""
    text = "srx configuration configure monitoring monitor security security"  # A task tie.
    result = SignalScorer().score(text)  # Score the tied-task sample.
    assert result.sub_category == "srx__security"  # The middle task segment is omitted.
    assert not any(key.startswith("task_type:") for key in result.scores)  # No task score.


def test_task_segment_stays_with_a_clear_lead() -> None:
    """The task segment stays when one task type leads by the margin (Defect B)."""
    text = "srx configuration configure config security"  # Configuration leads clearly.
    result = SignalScorer().score(text)  # Score the configuration-led sample.
    assert result.sub_category == "srx__configuration__security"  # The task segment stays.


def test_gpu_cluster_signal_wins_for_ai_vocabulary() -> None:
    """The GPU cluster signal wins for AI data-center vocabulary (Defect C)."""
    text = "qfx gpu gpus rdma roce nccl backend fabric training configuration"  # AI vocab.
    result = SignalScorer().score(text)  # Score the AI cluster sample.
    assert "gpu-cluster" in result.detected_signals  # The GPU cluster signal is present.


def test_evpn_vxlan_signal_wins_for_fabric_vocabulary() -> None:
    """The EVPN VXLAN signal wins for data-center fabric vocabulary (Defect C)."""
    text = "qfx evpn vxlan vtep vni multitenancy configuration"  # EVPN VXLAN vocab.
    result = SignalScorer().score(text)  # Score the fabric sample.
    assert "evpn-vxlan" in result.detected_signals  # The EVPN VXLAN signal is present.


def test_score_is_comparable_across_lengths() -> None:
    """The normalized score depends on density, not on length (Defect D)."""
    short = SignalScorer().score("srx security " * 100)  # A short, dense sample.
    long = SignalScorer().score("srx security " * 400)  # The same density, four times longer.
    assert short.sub_category == long.sub_category  # The label does not change with length.
    assert abs(sum(short.scores.values()) - sum(long.scores.values())) < 0.01  # Equal strength.


def test_sparse_long_document_falls_back() -> None:
    """A long sample with few signals falls back at the default threshold (Defect D)."""
    text = "srx " + "network design overview " * 500  # One product hit in a long body.
    result = SignalScorer().score(text)  # Score the sparse sample with the default threshold.
    assert result.is_fallback is True  # The low-density sample yields the fallback label.


def test_result_holds_no_body_text() -> None:
    """The result carries the label, the signal names, and the scores only (FR-024)."""
    text = "srx configuration security firewall routing"  # A sample with a rare token.
    result = SignalScorer().score(text, "jvd-wan-edge-for-srx.pdf")  # Score the sample.
    assert text not in result.sub_category  # The label holds no body text.
    assert all("firewall" != signal for signal in result.detected_signals)  # Names only.
