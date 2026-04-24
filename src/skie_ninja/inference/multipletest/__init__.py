"""Multiple-testing procedures across a strategy universe.

Currently implements Hansen 2005 Superior Predictive Ability (SPA)
test for the composite null "no strategy in the candidate set beats
the benchmark".  Future work will add Romano-Wolf 2005 step-down
per ADR-0003.
"""

from skie_ninja.inference.multipletest.hansen_spa import (
    HansenSPAResult,
    hansen_spa_test,
)

__all__ = [
    "HansenSPAResult",
    "hansen_spa_test",
]
