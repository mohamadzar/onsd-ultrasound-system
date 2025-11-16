import pytest
import sys
import os
from unittest.mock import Mock
import numpy as np

# Add the project root to Python path
projeultra_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, projeultra_root)

from ultra_app.domain.entities import CaptureSlot, OperationState, Measurement, PatientReport, EyeMeasurements
from ultra_app.domain.policies import SixImagesPolicy
from ultra_app.domain.ports import ProcessorGateway, ReportWriterPort


@pytest.fixture
def sample_capture_slots():
    return [
        CaptureSlot("Right", 1),
        CaptureSlot("Right", 2),
        CaptureSlot("Right", 3),
        CaptureSlot("Left", 1),
        CaptureSlot("Left", 2),
        CaptureSlot("Left", 3),
    ]


@pytest.fixture
def sample_operation_state(sample_capture_slots):
    return OperationState(order=sample_capture_slots)


@pytest.fixture
def sample_measurements():
    return [
        Measurement(
            image_stem="01_16",
            status="meas_ok",
            ond_px=40.0,
            onsd_px=79.0,
            ond_mm=1.2,
            onsd_mm=2.37,
            depth_mm=0.54,
            latency_s=0.76,
            time="12:00:00"
        ),
        Measurement(
            image_stem="01_17",
            status="meas_ok",
            ond_px=27.0,
            onsd_px=73.0,
            ond_mm=0.81,
            onsd_mm=2.19,
            depth_mm=0.51,
            latency_s=0.745,
            time="12:01:00"
        ),
    ]


@pytest.fixture
def sample_patient_report():
    measurements = [
        Measurement(onsd_mm=2.37, ond_mm=1.2, status="meas_ok"),
        Measurement(onsd_mm=2.19, ond_mm=0.81, status="meas_ok"),
        Measurement(onsd_mm=4.92, ond_mm=1.98, status="meas_ok"),
        Measurement(onsd_mm=4.92, ond_mm=1.98, status="meas_ok"),
        Measurement(onsd_mm=4.92, ond_mm=1.98, status="meas_ok"),
        Measurement(onsd_mm=2.31, ond_mm=0.03, status="meas_ok"),
    ]
    
    right_eye = EyeMeasurements(measurements=measurements[:3])
    left_eye = EyeMeasurements(measurements=measurements[3:])
    
    return PatientReport(
        patient_id="TEST001",
        right_eye=right_eye,
        left_eye=left_eye
    )


@pytest.fixture
def mock_processor():
    processor = Mock(spec=ProcessorGateway)
    processor.process.return_value = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    return processor


@pytest.fixture
def mock_report_writer():
    writer = Mock(spec=ReportWriterPort)
    writer.save_report.return_value = ("test_report.png", "test_report.pdf")
    return writer


@pytest.fixture
def sample_images():
    return [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(6)]