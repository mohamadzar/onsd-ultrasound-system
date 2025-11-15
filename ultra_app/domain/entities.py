from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np
from datetime import datetime


@dataclass(frozen=True)
class CaptureSlot:
    eye: str  # "Right" or "Left"
    index_in_eye: int  # 1..3


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


@dataclass
class Measurement:
    """Domain entity representing a single measurement CSV row."""
    image_stem: Optional[str] = None
    status: Optional[str] = None
    ond_px: Optional[float] = None
    onsd_px: Optional[float] = None
    ond_mm: Optional[float] = None
    onsd_mm: Optional[float] = None
    depth_mm: Optional[float] = None
    latency_s: Optional[float] = None
    time: Optional[str] = None
    raw: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = dict(self.raw)
        d.update({
            "image_stem": self.image_stem,
            "status": self.status,
            "ond_px": self.ond_px,
            "onsd_px": self.onsd_px,
            "ond_mm": self.ond_mm,
            "onsd_mm": self.onsd_mm,
            "depth_mm": self.depth_mm,
            "latency_s": self.latency_s,
            "time": self.time,
        })
        return d


@dataclass
class EyeMeasurements:
    """Container for all measurements of a single eye (3 images)"""
    measurements: List[Measurement] = field(default_factory=list)

    @property
    def average_onsd_mm(self) -> Optional[float]:
        valid_values = [m.onsd_mm for m in self.measurements if m.onsd_mm is not None]
        if not valid_values:
            return None
        return round(sum(valid_values) / len(valid_values), 2)

    @property
    def average_ond_mm(self) -> Optional[float]:
        valid_values = [m.ond_mm for m in self.measurements if m.ond_mm is not None]
        if not valid_values:
            return None
        return round(sum(valid_values) / len(valid_values), 2)


@dataclass
class PatientReport:
    """Complete report data for a patient"""
    patient_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    right_eye: EyeMeasurements = field(default_factory=EyeMeasurements)
    left_eye: EyeMeasurements = field(default_factory=EyeMeasurements)

    @property
    def all_measurements(self) -> List[Measurement]:
        """Returns all measurements in order: R1, R2, R3, L1, L2, L3"""
        return self.right_eye.measurements[:3] + self.left_eye.measurements[:3]

    @property
    def onsd_values(self) -> List[Optional[float]]:
        return [m.onsd_mm for m in self.all_measurements]

    @property
    def ond_values(self) -> List[Optional[float]]:
        return [m.ond_mm for m in self.all_measurements]

    @property
    def capture_times(self) -> List[Optional[str]]:
        return [m.time or "—" for m in self.all_measurements]

    @property
    def status_values(self) -> List[Optional[str]]:
        return [m.status or "—" for m in self.all_measurements]


@dataclass
class ReportData:
    """Complete data needed to generate a report"""
    patient_report: PatientReport
    right_images: List[Optional[np.ndarray]]
    left_images: List[Optional[np.ndarray]]

    def __post_init__(self):
        # Ensure we have exactly 3 images per eye
        self.right_images = list(self.right_images[:3]) + [None] * max(0, 3 - len(self.right_images))
        self.left_images = list(self.left_images[:3]) + [None] * max(0, 3 - len(self.left_images))

    @property
    def all_images(self) -> List[Optional[np.ndarray]]:
        return self.right_images + self.left_images