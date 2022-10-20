from dataclasses import dataclass

from structure_scripts.aisc_360_10.criteria import DesignStrength


@dataclass
class LateralTorsionalBuckling(DesignStrength):
    pass
