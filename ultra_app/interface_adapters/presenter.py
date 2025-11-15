from ultra_app.use_cases.capture_controller import CaptureController

class OperationPresenter:
    """Transforms use-case state into simple view data for the GUI."""
    def to_view(self, controller: CaptureController) -> dict:
        cur, total = controller.progress_vector()
        next_lbl = controller.next_expected_label()
        return {
            "progress_text": "Vector {} / {} • {}".format(cur, total, next_lbl),
            "can_export": controller.is_complete(),
        }
