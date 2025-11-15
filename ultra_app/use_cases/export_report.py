# ultra_app/use_cases/export_report.py
from __future__ import annotations

from typing import Tuple, Optional, List

from ultra_app.domain.entities import OperationState
from ultra_app.domain.ports import ReportWriterPort
from ultra_app.interface_adapters.measurement_loader import MeasurementLoader


class ExportReport:
    """
    Thin use-case wrapper that delegates to the ReportWriter adapter.
    Uses captured images from screen but measurement values from CSV.
    """

    def __init__(self, writer: ReportWriterPort):
        self.writer = writer

    def export(
            self,
            state: OperationState,
            out_dir: str,
            onsd_values: Optional[List[Optional[float]]] = None,
            capture_times: Optional[List[str]] = None,
            patient_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Returns (png_path, pdf_path).
        Uses captured images from screen but measurement values from CSV.
        """
        if not state.is_complete():
            raise RuntimeError("Capture all 6 images before exporting.")

        if onsd_values is None and hasattr(state, "onsd_values"):
            onsd_values = getattr(state, "onsd_values")
        if capture_times is None and hasattr(state, "capture_times"):
            capture_times = getattr(state, "capture_times")

        return self.writer.save_report(
            images_right=state.images_right,
            images_left=state.images_left,
            out_dir=out_dir,
            onsd_values=onsd_values,
            capture_times=capture_times,
            patient_id=patient_id,
        )

    def export_with_csv_measurements(
            self,
            images_right: List,
            images_left: List,
            measurements_csv: str,
            out_dir: str,
            patient_id: Optional[str] = None,
            capture_times: Optional[List[str]] = None,
            debug: bool = False,
    ) -> Tuple[str, str]:
        """Generate a report using captured images but measurement values from CSV.
        ALWAYS uses provided capture times instead of CSV times.
        """
        # load up to 6 measurement rows from CSV
        loader = MeasurementLoader(measurements_csv)
        measurements = loader.load_measurements(max_rows=6)

        if debug:
            print("[export_with_csv_measurements] Loaded measurements:")
            for i, m in enumerate(measurements, 1):
                print(f"  {i}: image_stem={m.image_stem!r}, onsd_mm={m.onsd_mm!r}")

        # Extract all measurement data for the report from CSV (EXCEPT TIMES)
        onsd_values = [m.onsd_mm for m in measurements]
        ond_values = [m.ond_mm for m in measurements]
        onsd_px_values = [m.onsd_px for m in measurements]
        ond_px_values = [m.ond_px for m in measurements]
        depth_values = [m.depth_mm for m in measurements]
        latency_values = [m.latency_s for m in measurements]
        status_values = [m.status for m in measurements]

        # ALWAYS USE PROVIDED CAPTURE TIMES OR DEFAULT
        if capture_times and len(capture_times) >= 6:
            final_capture_times = capture_times[:6]
        else:
            # Create default times if none provided
            final_capture_times = [f"12:0{i}:00" for i in range(6)]

        # Pad lists to ensure we have 6 entries
        while len(onsd_values) < 6:
            onsd_values.append(None)
        while len(ond_values) < 6:
            ond_values.append(None)
        while len(onsd_px_values) < 6:
            onsd_px_values.append(None)
        while len(ond_px_values) < 6:
            ond_px_values.append(None)
        while len(depth_values) < 6:
            depth_values.append(None)
        while len(latency_values) < 6:
            latency_values.append(None)
        while len(status_values) < 6:
            status_values.append(None)
        while len(final_capture_times) < 6:
            final_capture_times.append("—")

        return self.writer.save_report(
            images_right=images_right,
            images_left=images_left,
            out_dir=out_dir,
            onsd_values=onsd_values,
            capture_times=final_capture_times,  # Always use actual capture times
            patient_id=patient_id,
            ond_values=ond_values,
            onsd_px_values=onsd_px_values,
            ond_px_values=ond_px_values,
            depth_values=depth_values,
            latency_values=latency_values,
            status_values=status_values,
        )