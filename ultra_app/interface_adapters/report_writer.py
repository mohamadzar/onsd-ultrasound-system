# ultra_app/interface_adapters/report_writer.py
from __future__ import annotations

import os
from io import BytesIO
from datetime import datetime
from typing import List, Optional, Tuple

import cv2
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


class ReportWriter:
    """
    Creates a single-page PDF + a PNG grid with real measurement data.
    Enhanced to show all measurement values from CSV.
    """

    def __init__(self, threshold_mm: float = 6.0):
        self.threshold_mm = float(threshold_mm)

    # ---------- public API ----------
    def save_report(
            self,
            images_right: List[np.ndarray],
            images_left: List[np.ndarray],
            out_dir: str,
            onsd_values: Optional[List[Optional[float]]] = None,
            capture_times: Optional[List[str]] = None,
            patient_id: Optional[str] = None,
            # Additional measurement data
            ond_values: Optional[List[Optional[float]]] = None,
            onsd_px_values: Optional[List[Optional[float]]] = None,
            ond_px_values: Optional[List[Optional[float]]] = None,
            depth_values: Optional[List[Optional[float]]] = None,
            latency_values: Optional[List[Optional[float]]] = None,
            status_values: Optional[List[Optional[str]]] = None,
    ) -> Tuple[str, str]:
        """
        Returns (png_path, pdf_path)
        """
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"report_{ts}"
        pdf_path = os.path.join(out_dir, f"{base_name}.pdf")
        png_path = os.path.join(out_dir, f"{base_name}.png")

        # Normalize lists
        right = list(images_right[:3]) + [None] * max(0, 3 - len(images_right))
        left = list(images_left[:3]) + [None] * max(0, 3 - len(images_left))
        imgs_all = right + left  # [R1,R2,R3,L1,L2,L3]

        # Normalize all measurement data
        if onsd_values is None:
            onsd_values = [None] * 6
        else:
            onsd_values = list(onsd_values[:6]) + [None] * max(0, 6 - len(onsd_values))

        if capture_times is None:
            capture_times = ["—"] * 6
        else:
            capture_times = list(capture_times[:6]) + ["—"] * max(0, 6 - len(capture_times))

        # Normalize additional data
        ond_values = self._normalize_list(ond_values, 6)
        onsd_px_values = self._normalize_list(onsd_px_values, 6)
        ond_px_values = self._normalize_list(ond_px_values, 6)
        depth_values = self._normalize_list(depth_values, 6)
        latency_values = self._normalize_list(latency_values, 6)
        status_values = self._normalize_list(status_values, 6, default="—")

        # Compute averages ignoring None
        r_vals = [v for v in onsd_values[:3] if v is not None]
        l_vals = [v for v in onsd_values[3:] if v is not None]
        right_avg = round(sum(r_vals) / len(r_vals), 2) if r_vals else None
        left_avg = round(sum(l_vals) / len(l_vals), 2) if l_vals else None

        # Build SINGLE-PAGE PDF with enhanced data
        self._build_pdf_single_page(
            pdf_path=pdf_path,
            patient_id=patient_id,
            imgs_all=imgs_all,
            onsd_values=onsd_values,
            capture_times=capture_times,
            right_avg=right_avg,
            left_avg=left_avg,
            # Pass additional data
            ond_values=ond_values,
            onsd_px_values=onsd_px_values,
            ond_px_values=ond_px_values,
            depth_values=depth_values,
            latency_values=latency_values,
            status_values=status_values,
        )

        # Build PNG grid (for convenience / preview)
        grid = self._build_png_grid(right, left)
        cv2.imwrite(png_path, grid)

        return (png_path, pdf_path)

    def _normalize_list(self, values, length: int, default=None):
        """Helper to normalize list to specified length."""
        if values is None:
            return [default] * length
        return list(values[:length]) + [default] * max(0, length - len(values))

    # ---------- helpers ----------
    def _np_to_imagereader(self, img: Optional[np.ndarray]) -> ImageReader:
        """Convert numpy image (BGR or grayscale) to ImageReader via JPEG bytes."""
        if img is None:
            # MAXIMIZED SIZE: Very large blank placeholder
            blank = np.full((300, 225, 3), 240, dtype=np.uint8)  # Increased to 300x225
            ok, buf = cv2.imencode(".jpg", blank)
        else:
            img3 = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img
            ok, buf = cv2.imencode(".jpg", img3)
        if not ok:
            raise RuntimeError("Failed to encode image for PDF.")
        return ImageReader(BytesIO(buf.tobytes()))

    def _avg_color(self, val: Optional[float]):
        if val is None:
            return colors.black
        # red if > threshold else blue-ish (#0a84ff)
        return colors.red if val > self.threshold_mm else colors.Color(0.04, 0.52, 1.0)

    def _draw_enhanced_table_and_return_y(
            self,
            c: canvas.Canvas,
            start_x: float,
            start_y: float,
            rows: List[Tuple[str, str, str, str, str, str, str, str]],
    ) -> float:
        """Draw the enhanced 6-row table with all measurement data."""
        headers = ["Image", "Eye", "Status", "ONSD (mm)", "OND (mm)", "ONSD (px)", "Depth (mm)", "Time"]
        col_w = [12 * mm, 12 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm]  # Reduced column widths
        row_h = 5 * mm  # Reduced row height from 7mm to 5mm

        # headers
        c.setFont("Helvetica-Bold", 9)
        x = start_x
        y = start_y
        for i, h in enumerate(headers):
            c.drawString(x + 1 * mm, y, h)
            x += col_w[i]

        # rows
        c.setFont("Helvetica", 8)
        y -= row_h
        for r in rows:
            x = start_x
            for i, cell in enumerate(r):
                c.drawString(x + 1 * mm, y, str(cell))
                x += col_w[i]
            y -= row_h

        return y

    def _build_pdf_single_page(
            self,
            pdf_path: str,
            patient_id: Optional[str],
            imgs_all: List[Optional[np.ndarray]],
            onsd_values: List[Optional[float]],
            capture_times: List[str],
            right_avg: Optional[float],
            left_avg: Optional[float],
            # Additional data
            ond_values: List[Optional[float]],
            onsd_px_values: List[Optional[float]],
            ond_px_values: List[Optional[float]],
            depth_values: List[Optional[float]],
            latency_values: List[Optional[float]],
            status_values: List[Optional[str]],
    ):
        c = canvas.Canvas(pdf_path, pagesize=A4)
        W, H = A4
        margin = 15 * mm
        inner_w = W - 2 * margin

        y = H - margin

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y, "Report: Automated ONSD Measurement")
        y -= 8 * mm

        # Meta row: Patient ID + Date
        c.setFont("Helvetica", 11)
        pid = (patient_id or "N/A")
        c.drawString(margin, y, f"Patient ID: {pid}")
        c.drawRightString(W - margin, y, f"Date: {datetime.now().strftime('%d.%m.%Y')}")
        y -= 10 * mm

        # Enhanced table rows (1..6) — RRR then LLL with all measurement data
        rows = []
        for i in range(6):
            eye = "R" if i < 3 else "L"
            img_num = str(i + 1)
            status = status_values[i] or "—"
            onsd_mm = f"{onsd_values[i]:.2f}" if isinstance(onsd_values[i], (int, float)) else "—"
            ond_mm = f"{ond_values[i]:.2f}" if isinstance(ond_values[i], (int, float)) else "—"
            onsd_px = f"{onsd_px_values[i]:.0f}" if isinstance(onsd_px_values[i], (int, float)) else "—"
            depth = f"{depth_values[i]:.2f}" if isinstance(depth_values[i], (int, float)) else "—"
            time_val = capture_times[i] if i < len(capture_times) else "—"

            rows.append((img_num, eye, status, onsd_mm, ond_mm, onsd_px, depth, time_val))

        # Draw the enhanced table
        y = self._draw_enhanced_table_and_return_y(c, start_x=margin, start_y=y, rows=rows)
        y -= 3 * mm  # small gap

        # Averages (color-coded)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "ONSD Averages:")
        # Right
        c.setFillColor(self._avg_color(right_avg))
        c.drawString(margin + 40 * mm, y, f"Right: {right_avg:.2f} mm" if right_avg is not None else "Right: —")
        # separator
        c.setFillColor(colors.black)
        c.drawString(margin + 75 * mm, y, "|")
        # Left
        c.setFillColor(self._avg_color(left_avg))
        c.drawString(margin + 80 * mm, y, f"Left: {left_avg:.2f} mm" if left_avg is not None else "Left: —")
        c.setFillColor(colors.black)

        y -= 8 * mm

        # Normal/Abnormal/Info line
        def is_normal(v: Optional[float]) -> bool:
            return v is not None and v <= self.threshold_mm

        c.setFont("Helvetica-Bold", 12)
        if (right_avg is not None and left_avg is not None) and (is_normal(right_avg) and is_normal(left_avg)):
            c.setFillColor(colors.green)
            c.drawString(margin, y, "✓ Normal finding. No indications of increased intracranial pressure.")
        else:
            c.setFillColor(colors.red)
            c.drawString(margin, y, "⚠ Abnormal finding. ONSD average exceeds threshold in at least one eye.")
        c.setFillColor(colors.black)

        y -= 8 * mm  # Reduced spacing

        # ----- Thumbnails -----
        bottom_limit = margin + 5 * mm  # Reduced bottom margin
        avail_h = y - bottom_limit

        # MAXIMIZED IMAGE SIZES: Use almost all available space
        rows = 3
        v_spacing = 3 * mm  # Minimal vertical spacing

        # Calculate maximum possible thumbnail height - use 90% of available height
        max_thumb_h = min(90 * mm, (avail_h - (rows - 1) * v_spacing) / rows)  # Increased to 90mm
        thumb_h = max_thumb_h
        thumb_w = thumb_h * 0.85  # Wider aspect ratio

        # Calculate total width needed for both columns
        total_images_width = 2 * thumb_w
        h_spacing = 15 * mm  # Reasonable spacing between columns

        # CENTER THE IMAGES: Calculate starting X position to center the images
        total_width_needed = total_images_width + h_spacing
        start_x = margin + (inner_w - total_width_needed) / 2

        col_x0 = start_x
        col_x1 = start_x + thumb_w + h_spacing

        # Column titles - centered and closer to images
        c.setFont("Helvetica-Bold", 10)
        c.drawString(col_x0, y, "Right Eye (R)")
        c.drawString(col_x1, y, "Left Eye (L)")
        y -= 4 * mm  # Minimal space between title and images

        # Draw Right column (0..2)
        yy = y
        for i in range(3):
            reader = self._np_to_imagereader(imgs_all[i])
            c.drawImage(reader, col_x0, yy - thumb_h, thumb_w, thumb_h, preserveAspectRatio=True, anchor='nw')
            yy -= (thumb_h + v_spacing)

        # Draw Left column (3..5)
        yy = y
        for i in range(3, 6):
            reader = self._np_to_imagereader(imgs_all[i])
            c.drawImage(reader, col_x1, yy - thumb_h, thumb_w, thumb_h, preserveAspectRatio=True, anchor='nw')
            yy -= (thumb_h + v_spacing)

        # Finish the single page
        c.save()

    def _build_png_grid(self, right: List[Optional[np.ndarray]], left: List[Optional[np.ndarray]]) -> np.ndarray:
        """Build a simple 2x3 grid PNG (Right column + Left column)."""

        def as_color(img):
            if img is None:
                # MAXIMIZED SIZE: Very large placeholder images
                return np.full((600, 450, 3), 240, dtype=np.uint8)  # Increased to 600x450
            # Resize image to fit in grid - MAXIMIZED SIZE
            return cv2.resize(img, (450, 600))  # Increased to 450x600

        # Create 3x2 grid (3 rows, 2 columns)
        grid_rows = []
        for i in range(3):
            row_imgs = []
            # Right eye image
            if i < len(right) and right[i] is not None:
                row_imgs.append(as_color(right[i]))
            else:
                row_imgs.append(as_color(None))

            # Left eye image  
            if i < len(left) and left[i] is not None:
                row_imgs.append(as_color(left[i]))
            else:
                row_imgs.append(as_color(None))

            # Concatenate horizontally with minimal spacing
            row = np.hstack(row_imgs)
            grid_rows.append(row)

        # Concatenate vertically with minimal spacing
        if grid_rows:
            grid = np.vstack(grid_rows)
        else:
            grid = as_color(None)

        return grid