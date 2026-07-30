"""US-6/NFR-3: canonical JSON is byte-stable; named errors carry a machine-readable reason."""

from __future__ import annotations

from aspark_insights.errors import (
    GraphNotBuiltError,
    GraphVersionMismatchError,
    NotImplementedStub,
    PolicyUnavailable,
    VerifyMismatchError,
)
from aspark_insights.serialization import canonical_json


def test_canonical_json_is_byte_stable_regardless_of_input_key_order():
    a = canonical_json({"b": 1, "a": 2, "nested": {"z": 1, "y": 2}})
    b = canonical_json({"a": 2, "nested": {"y": 2, "z": 1}, "b": 1})
    assert a == b
    assert a.endswith("\n")


def test_canonical_json_does_not_escape_non_ascii():
    assert "ü" in canonical_json({"note": "ü"})


def test_named_errors_carry_machine_readable_reason():
    for cls, expected_reason in [
        (GraphNotBuiltError, "graph_not_built"),
        (GraphVersionMismatchError, "graph_version_mismatch"),
        (PolicyUnavailable, "policy_unavailable"),
        (NotImplementedStub, "not_implemented"),
        (VerifyMismatchError, "verify_mismatch"),
    ]:
        err = cls("something went wrong")
        d = err.to_dict()
        assert d["error"] == expected_reason
        assert d["message"] == "something went wrong"
