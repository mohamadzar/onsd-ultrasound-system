from typing import Tuple


from ultra_app.domain.entities import OperationState


from ultra_app.domain.ports import ReportWriterPort





class ExportReport:


    def __init__(self, writer: ReportWriterPort):


        self.writer = writer





    def export(self, state: OperationState, out_dir: str) -> Tuple[str, str]:


        if not state.is_complete():


            raise RuntimeError("Capture all 6 images before exporting.")


        return self.writer.save_report(state.images_right, state.images_left, out_dir)