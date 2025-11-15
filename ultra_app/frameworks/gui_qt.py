# ultra_app/interface_adapters/view_qt.py
from __future__ import annotations

import sys
import time
from typing import Optional, List
import numpy as np
import cv2
from datetime import datetime
import getpass
import os

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QFrame, QLineEdit
)

from ultra_app.use_cases.capture_controller import CaptureController
from ultra_app.use_cases.export_report import ExportReport
from ultra_app.interface_adapters.presenter import OperationPresenter
from ultra_app.interface_adapters.camera_opencv import OpenCVCamera

ACCENT = "#5ac8fa"
BG = "#0f1115"
CARD = "#171a21"
TEXT = "#e6ebf0"
TEXT_DIM = "#a9b2bd"
BORDER = "#2a2f3a"


def _apply_global_style(app: QApplication):
    app.setStyleSheet(f"""
        QWidget {{
            background: {BG};
            color: {TEXT};
            font-family: 'Segoe UI', 'Inter', system-ui, -apple-system, Arial;
            font-size: 14px;
        }}
        QLabel#title {{ font-size: 20px; font-weight: 700; }}
        QLabel#badge {{
            background: {CARD};
            color: {TEXT};
            border: 1px solid {BORDER};
            padding: 6px 10px;
            border-radius: 10px;
            font-weight: 600;
        }}
        QFrame#card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 14px;
        }}
        QLabel#previewTitle {{ color: {TEXT_DIM}; font-weight: 600; padding: 6px 10px; }}
        QPushButton {{
            background: #1e232e;
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 10px 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{ border-color: {ACCENT}; }}
        QPushButton:disabled {{ color: #7b8591; border-color: #242a34; }}
        QPushButton#primary {{ background: {ACCENT}; color: #0a0c10; border: none; }}
        QPushButton#secondary {{ background: #1b212c; }}
        QLabel#thumb {{
            background: #0b0e13;
            color: {TEXT_DIM};
            border: 1px dashed {BORDER};
            border-radius: 10px;
        }}
    """)


class ULTRAWindow(QWidget):
    def __init__(self, controller: CaptureController, exporter: ExportReport,
                 presenter: OperationPresenter, camera: OpenCVCamera):
        super().__init__()
        self.setWindowTitle("ULTRA Eye Scan – Clean Architecture")
        self.controller = controller
        self.exporter = exporter
        self.presenter = presenter
        self.camera = camera

        # Header
        header = QHBoxLayout()
        self.title = QLabel("ULTRA Eye Scan Simulator")
        self.title.setObjectName("title")
        self.badge_status = QLabel("LIVE")
        self.badge_status.setObjectName("badge")
        # You can set this to any patient label you like; shown text will be used in PDF.
        self.badge_id = QLineEdit(f"{getpass.getuser()}")
        self.badge_id.setObjectName("badge")
        self.badge_id.setMaximumWidth(180)
        self.badge_id.setAlignment(Qt.AlignCenter)
        self.badge_date = QLabel(datetime.now().strftime("%Y-%m-%d"))
        self.badge_date.setObjectName("badge")
        self.badge_fps = QLabel("FPS: --")
        self.badge_fps.setObjectName("badge")
        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(self.badge_status)
        header.addWidget(self.badge_id)
        header.addWidget(self.badge_date)
        header.addWidget(self.badge_fps)

        # Live/Processed view
        self.seg_label = QLabel("–")
        self.seg_label.setAlignment(Qt.AlignCenter)
        self.seg_label.setMinimumSize(640, 360)

        # Controls
        self.btn_capture = QPushButton("● Capture  (Space)")
        self.btn_capture.setObjectName("primary")
        self.btn_capture.setMinimumHeight(44)
        # Side indicator: shows "R" for Right images (first 3) and "L" for Left images (last 3)
        self.side_label = QLabel("")
        self.side_label.setObjectName("badge")
        self.side_label.setFixedWidth(26)
        self.side_label.setAlignment(Qt.AlignCenter)
        self.btn_save = QPushButton("✔ Save")
        self.btn_save.setObjectName("primary")
        self.btn_save.hide()
        self.btn_delete = QPushButton("✖ Delete")
        self.btn_delete.setObjectName("secondary")
        self.btn_delete.hide()

        controls = QHBoxLayout()
        controls.addWidget(self.btn_capture)
        controls.addWidget(self.side_label)
        controls.addWidget(self.btn_save)
        controls.addWidget(self.btn_delete)
        controls.addStretch(1)

        # Root
        root = QVBoxLayout(self)
        root.addLayout(header)
        root.addWidget(self.seg_label, 1)
        root.addLayout(controls)

        # events
        self.btn_capture.clicked.connect(self.on_capture)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_delete.clicked.connect(self.on_delete)

        # shortcuts
        QShortcut(QKeySequence("Space"), self, activated=self.on_capture)

        # timer (video)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_frame)
        self.timer.start(30)  # ~33 FPS

        self.current_frame: Optional[np.ndarray] = None
        self._last_ts = time.time()
        self._frames = 0

        self.captured_images: List[np.ndarray] = []
        self.capture_index = 0
        self.in_review = False

        # per-shot data for report
        self.onsd_values: List[Optional[float]] = []
        self.capture_times: List[str] = []

        self.update_ui()

    def _update_side_label(self):
        """Set the side label to 'R' or 'L' depending on the controller next_expected_label().
        Empty when capture is complete.
        """
        try:
            if self.controller.is_complete():
                self.side_label.setText("")
                return
            nxt = self.controller.next_expected_label()
            # next_expected_label returns something like 'Right #1' or 'Left #2'
            if nxt.lower().startswith("right"):
                self.side_label.setText("R")
            elif nxt.lower().startswith("left"):
                self.side_label.setText("L")
            else:
                self.side_label.setText("")
        except Exception:
            # Fallback to empty on any error
            self.side_label.setText("")

    # ---------- Image helpers ----------
    def _cv_to_qpix(self, frame: np.ndarray) -> QPixmap:
        if frame.ndim == 2:
            rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg.copy())

    def _scaled_pix(self, frame: np.ndarray, target: QLabel) -> QPixmap:
        return self._cv_to_qpix(frame).scaled(
            target.width(), target.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

    # ---------- Timer ----------
    def on_frame(self):
        if self.in_review:
            return
        frame = self.camera.read()
        if frame is None:
            self.badge_status.setText("NO SIGNAL")
            return
        self.badge_status.setText("LIVE")
        self.current_frame = frame
        proc = self.controller.process_only(frame)
        self.seg_label.setPixmap(self._scaled_pix(proc, self.seg_label))

        # FPS
        self._frames += 1
        now = time.time()
        if now - self._last_ts >= 1.0:
            fps = self._frames / (now - self._last_ts)
            self.badge_fps.setText(f"FPS: {fps:.1f}")
            self._frames = 0
            self._last_ts = now

    # ---------- Buttons ----------
    def on_capture(self):
        if self.current_frame is None or self.in_review:
            return
        try:
            proc = self.controller.process_only(self.current_frame)
            self.review_image = proc.copy()
            self.in_review = True
            self.update_ui()
        except Exception as e:
            QMessageBox.warning(self, "Capture error", str(e))

    def on_save(self):
        if self.current_frame is None:
            return
        try:
            # Commit the capture to controller/state
            self.controller.capture(self.current_frame)

            # Keep the processed image for thumbnails
            self.captured_images.append(self.review_image)

            # ONSD & Time: time is captured **when Save is clicked**
            onsd_value = None
            try:
                onsd_value = self.controller.processor.get_last_onsd_value()
            except Exception:
                pass
            self.onsd_values.append(onsd_value)

            # CAPTURE THE AULTRAUAL TIMESTAMP WHEN IMAGE IS SAVED
            current_time = datetime.now().strftime('%H:%M:%S')
            self.capture_times.append(current_time)  # Use actual capture time

            self.capture_index += 1
            self.in_review = False

            # Check if all 6 images are captured
            if self.capture_index >= 6:
                out_dir = QFileDialog.getExistingDirectory(self, "Choose where to save the report")
                if out_dir:
                    try:
                        patient_id = self.badge_id.text().strip()

                        # USE CAPTURED IMAGES FROM SCREEN + MEASUREMENTS FROM CSV + AULTRAUAL TIMESTAMPS
                        images_dir = "Measurement Results"
                        measurements_csv = os.path.join(images_dir, "measure_log.csv")

                        if os.path.exists(measurements_csv):
                            # Use captured images with CSV measurements BUT AULTRAUAL CAPTURE TIMES
                            png_path, pdf_path = self.exporter.export_with_csv_measurements(
                                images_right=self.controller.state.images_right,
                                images_left=self.controller.state.images_left,
                                measurements_csv=measurements_csv,
                                out_dir=out_dir,
                                patient_id=patient_id,
                                # Pass the actual capture times instead of CSV times
                                capture_times=self.capture_times
                            )

                            QMessageBox.information(
                                self, "Report Saved",
                                f"Report saved successfully!\n"
                                f"Images: Captured from screen\n"
                                f"Measurements: Loaded from CSV\n"
                                f"Timestamps: Actual capture times\n"
                                f"Image: {os.path.basename(png_path)}\n"
                                f"PDF: {os.path.basename(pdf_path)}"
                            )
                        else:
                            QMessageBox.warning(self, "CSV Not Found",
                                                f"Measurement CSV not found.\n"
                                                f"Looking for: {measurements_csv}")
                    except Exception as e:
                        QMessageBox.warning(self, "Save Error", f"Error saving report: {str(e)}")

                # AUTOMATICALLY RESET TO INITIAL STATE AFTER REPORT GENERATION
                self.reset_to_initial_state()
                return

            self.update_ui()

        except Exception as e:
            QMessageBox.warning(self, "Save error", str(e))

    def on_delete(self):
        self.in_review = False
        self.update_ui()

    def reset_to_initial_state(self):
        """Reset the application to initial state automatically"""
        try:
            # Reset controller state
            self.controller.reset()

            # Reset GUI state
            self.captured_images = []
            self.capture_index = 0
            self.in_review = False
            self.onsd_values = []
            self.capture_times = []

            # Update UI
            self.update_ui()

            # Show ready message
            self.badge_status.setText("LIVE")

        except Exception as e:
            QMessageBox.warning(self, "Reset Error", f"Error resetting session: {str(e)}")

    # ---------- UI sync ----------
    def update_ui(self):
        if self.in_review:
            self.timer.stop()
            self.seg_label.setPixmap(self._scaled_pix(self.review_image, self.seg_label))
            self.btn_capture.hide()
            self.btn_save.show()
            self.btn_delete.show()
        else:
            self.timer.start(30)
            self.btn_capture.show()
            self.btn_save.hide()
            self.btn_delete.hide()
        # keep the R/L indicator in sync
        self._update_side_label()

        # Update capture button text based on progress
        if self.controller.is_complete():
            self.btn_capture.setText("● Complete - Generating Report...")
            self.btn_capture.setEnabled(False)
        else:
            self.btn_capture.setText(f"● Capture ({self.capture_index + 1}/6)  (Space)")
            self.btn_capture.setEnabled(True)

    # ---------- Close ----------
    def closeEvent(self, e):
        try:
            self.camera.release()
        finally:
            super().closeEvent(e)


def run_gui(controller: CaptureController, exporter: ExportReport,
            presenter: OperationPresenter, camera: OpenCVCamera):
    app = QApplication(sys.argv)
    _apply_global_style(app)
    w = ULTRAWindow(controller, exporter, presenter, camera)
    w.resize(1380, 920)
    w.show()
    sys.exit(app.exec())