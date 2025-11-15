from typing import Tuple
import numpy as np
from ultra_app.domain.entities import OperationState
from ultra_app.domain.policies import SixImagesPolicy
from ultra_app.domain.ports import ProcessorGateway

class CaptureController:
    """
    Use-case layer: orchestrates the 6-image capture flow.
    - Does not own the camera (GUI provides frames for live/processed view).
    - Uses the ProcessorGateway to produce the processed image.
    """
    def __init__(self, processor: ProcessorGateway, policy: SixImagesPolicy):
        self.processor = processor
        self.policy = policy
        self.state = OperationState(order=self.policy.initial_order())

    # ---- Queries (for GUI) ----
    def progress_vector(self) -> Tuple[int, int]:
        # (current_index_1_based, total)
        cur = min(self.state.cursor + 1, self.state.total)
        return cur, self.state.total

    def is_complete(self) -> bool:
        return self.state.is_complete()

    def next_expected_label(self) -> str:
        if self.state.is_complete():
            return "Completed"
        slot = self.state.current_slot()
        return f"{slot.eye} #{slot.index_in_eye}"

    def process_only(self, frame: np.ndarray) -> np.ndarray:
        """Return processed preview without mutating state."""
        return self.processor.process(frame)

    # ---- Commands ----
    def capture(self, frame: np.ndarray) -> None:
        if self.state.is_complete():
            raise RuntimeError("All 6 images already captured.")
        processed = self.processor.process(frame)
        self.policy.store_image(self.state, processed)

    def undo(self) -> None:
        if self.state.cursor == 0:
            return
        # Move cursor back, then pop from the appropriate list
        self.state.cursor -= 1
        slot = self.state.order[self.state.cursor]
        if slot.eye == "Right" and self.state.images_right:
            self.state.images_right.pop()
        elif slot.eye == "Left" and self.state.images_left:
            self.state.images_left.pop()

    def reset(self) -> None:
        self.state = OperationState(order=self.policy.initial_order())
