from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
from datetime import datetime


dataclass(frozen=True)
class CaptureSlot:
    eye: str            # "Right" or "Left"
    index_in_eye: int   # 1..3


@dataclass
class OperationState:
    order: List[CaptureSlot]
    cursor: int = 0
    images_right: List[np.ndarray] = field(default_factory=list)
    images_left: List[np.ndarray] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.order)

    def is_complete(self) -> bool:
        return self.cursor >= self.total

    def current_slot(self) -> CaptureSlot:
        return self.order[self.cursor]

    def advance(self) -> None:
        self.cursor += 1