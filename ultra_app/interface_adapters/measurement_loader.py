"""CSV loader adapter that returns domain Measurement entities."""
from __future__ import annotations

import csv
import os
from typing import List, Optional
from datetime import datetime

from ultra_app.domain.entities import Measurement, PatientReport, EyeMeasurements


def _normalize_col(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def _to_float(s: Optional[str]) -> Optional[float]:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


class MeasurementLoader:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path

    def load_measurements(self, max_rows: Optional[int] = None) -> List[Measurement]:
        """Load raw measurements from CSV"""
        if not os.path.isfile(self.csv_path):
            raise FileNotFoundError(self.csv_path)

        with open(self.csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []
            norm_map = {_normalize_col(h): h for h in headers}

            def pick(*cands):
                for c in cands:
                    if c in norm_map:
                        return norm_map[c]
                # fallback: pick header that contains the candidate
                for c in cands:
                    for nk, orig in norm_map.items():
                        if c in nk:
                            return orig
                return None

            img_col = pick("imagestem", "image", "filename")
            status_col = pick("status")
            ondpx_col = pick("ondpx", "ond_px", "ond")
            onsdpx_col = pick("onsdpx", "onsd_px")
            ondmm_col = pick("ondmm", "ond_mm")
            onsdmm_col = pick("onsdmm", "onsd_mm", "onsd")
            depth_col = pick("depthmm", "depth_mm", "depth")
            latency_col = pick("latencys", "latency_s", "latency")
            time_col = pick("time", "capturetime", "timestamp")

            out: List[Measurement] = []
            for i, row in enumerate(reader):
                if max_rows is not None and i >= max_rows:
                    break

                raw = dict(row)
                m = Measurement(
                    image_stem=row.get(img_col) if img_col else None,
                    status=row.get(status_col) if status_col else None,
                    ond_px=_to_float(row.get(ondpx_col)) if ondpx_col else None,
                    onsd_px=_to_float(row.get(onsdpx_col)) if onsdpx_col else None,
                    ond_mm=_to_float(row.get(ondmm_col)) if ondmm_col else None,
                    onsd_mm=_to_float(row.get(onsdmm_col)) if onsdmm_col else None,
                    depth_mm=_to_float(row.get(depth_col)) if depth_col else None,
                    latency_s=_to_float(row.get(latency_col)) if latency_col else None,
                    time=row.get(time_col) if time_col else None,
                    raw=raw,
                )
                out.append(m)

        return out

    def load_patient_report(self, patient_id: str, max_rows: int = 6) -> PatientReport:
        """Load measurements and organize into PatientReport dataclass"""
        measurements = self.load_measurements(max_rows=max_rows)

        # Split into right and left eye measurements (first 3 are right, next 3 are left)
        right_measurements = measurements[:3]
        left_measurements = measurements[3:6]

        # Pad with empty measurements if needed
        while len(right_measurements) < 3:
            right_measurements.append(Measurement())
        while len(left_measurements) < 3:
            left_measurements.append(Measurement())

        return PatientReport(
            patient_id=patient_id,
            right_eye=EyeMeasurements(measurements=right_measurements),
            left_eye=EyeMeasurements(measurements=left_measurements)
        )