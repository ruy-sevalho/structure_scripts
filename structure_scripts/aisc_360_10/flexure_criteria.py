from dataclasses import dataclass

from structure_scripts.aisc_360_10.criteria import Criteria


@dataclass
class LateralTorsionalBuckling(Criteria):
    limit