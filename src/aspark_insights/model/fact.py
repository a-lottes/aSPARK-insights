"""Fact — a single observation about a system, feature or code artifact.

SubjectKind has no person-level member by construction (AC-4.1). This is not a
convention to remember: there is no enum value to reach for that would let a
metric key a Fact to an individual (a commit author, an assignee). Adding one
back would be the review-visible act of reopening a design constraint the
family treats as non-negotiable, not an accidental one-line slip.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SubjectKind(Enum):
    SYSTEM = "system"
    FEATURE = "feature"
    CODE_ARTIFACT = "code_artifact"


@dataclass(frozen=True, slots=True)
class Fact:
    subject_kind: SubjectKind
    subject_id: str
    predicate: str
    value: object

    def to_dict(self) -> dict:
        return {
            "subject_kind": self.subject_kind.value,
            "subject_id": self.subject_id,
            "predicate": self.predicate,
            "value": self.value,
        }
