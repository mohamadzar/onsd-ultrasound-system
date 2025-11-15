from typing import List
from .entities import CaptureSlot, OperationState
import numpy as np

class SixImagesPolicy:
    """Fixed sequence: Right 1..3, then Left 1..3."""
    def initial_order(self) -> List[CaptureSlot]:
        return [CaptureSlot("Right", i) for i in range(1, 4)] + \
               [CaptureSlot("Left",  i) for i in range(1, 4)]

    def store_image(self, state: OperationState, processed: np.ndarray) -> None:
        slot = state.current_slot()
        if slot.eye == "Right":
            state.images_right.append(processed)
        else:
            state.images_left.append(processed)
        state.advance()
