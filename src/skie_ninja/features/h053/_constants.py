"""Shared constants for H053 feature blocks (DRY).

These constants are referenced by multiple feature modules under
``src/skie_ninja/features/h053/`` (currently ``mediator.py`` and
``daily.py``). Centralising eliminates a future-drift risk if
documentation in one module is updated without the other.
"""

from __future__ import annotations

import math


# Garman-Klass simple-form C/O coefficient.
# justify: 2·ln(2) − 1 ≈ 0.3862944 is the closed-form coefficient on
# log(C/O)² in the Garman-Klass simple-form variance estimator
# (Garman & Klass 1980, J. Business 53(1):67-78,
# DOI 10.1086/296072). The exact equation-number anchor is paywall-
# unverified; tracked under follow-up
# ``P1-GK1980-EQ6-PRIMARY-VERIFY``. The formula coefficients are
# independently verified against multiple peer-reviewed secondary
# sources; substance is correct.
GK_C_OVER_O_COEF: float = 2.0 * math.log(2.0) - 1.0


__all__ = ["GK_C_OVER_O_COEF"]
