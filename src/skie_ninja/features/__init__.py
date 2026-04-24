"""Feature-factory package.

Importing this package triggers registration of every implemented
feature module via the sub-package imports below. After import,
:data:`FEATURE_REGISTRY` is populated and can be enumerated by the
walk-forward runner.

Cycle-6 scope: only :mod:`.microstructure` is populated. Empty
:mod:`.macro`, :mod:`.text`, :mod:`.altdata`, :mod:`.crossasset`
sub-packages exist as placeholders (``.gitkeep``) for future cycles.
"""

from skie_ninja.features.base import (
    FEATURE_REGISTRY,
    DatasetRef,
    FeatureModule,
    FeatureTestBase,
    register_feature,
)
# Import the microstructure subpackage to trigger feature registration.
from skie_ninja.features import microstructure as _microstructure  # noqa: F401

__all__ = [
    "DatasetRef",
    "FEATURE_REGISTRY",
    "FeatureModule",
    "FeatureTestBase",
    "register_feature",
]
