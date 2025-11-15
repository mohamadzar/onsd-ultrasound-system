from typing import Protocol, List, Optional
import numpy as np
from ultra_app.domain.entities import ReportData

class ProcessorGateway(Protocol):
    def process(self, frame: np.ndarray) -> np.ndarray: ...

class ReportWriterPort(Protocol):
    def save_report(self, report_data: ReportData, out_dir: str) -> tuple[str, str]: ...