import pytest
import numpy as np
from datetime import datetime
from ultra_app.domain.entities import CaptureSlot, OperationState, Measurement, EyeMeasurements, PatientReport


class TestCaptureSlot:
    def test_capture_slot_creation(self):
        slot = CaptureSlot("Right", 1)
        assert slot.eye == "Right"
        assert slot.index_in_eye == 1
    
    def test_capture_slot_immutable(self):
        slot = CaptureSlot("Left", 2)
        with pytest.raises(AttributeError):
            slot.eye = "Right"


class TestOperationState:
    def test_operation_state_initialization(self, sample_capture_slots):
        state = OperationState(order=sample_capture_slots)
        assert state.total == 6
        assert state.cursor == 0
        assert len(state.images_right) == 0
        assert len(state.images_left) == 0
    
    def test_is_complete(self, sample_operation_state):
        state = sample_operation_state
        assert not state.is_complete()
        
        state.cursor = 6
        assert state.is_complete()
        
        state.cursor = 7
        assert state.is_complete()
    
    def test_current_slot(self, sample_operation_state):
        state = sample_operation_state
        assert state.current_slot().eye == "Right"
        assert state.current_slot().index_in_eye == 1
        
        state.cursor = 3
        assert state.current_slot().eye == "Left"
        assert state.current_slot().index_in_eye == 1
    
    def test_advance(self, sample_operation_state):
        state = sample_operation_state
        initial_cursor = state.cursor
        state.advance()
        assert state.cursor == initial_cursor + 1


class TestMeasurement:
    def test_measurement_creation(self):
        measurement = Measurement(
            image_stem="test_image",
            status="meas_ok",
            onsd_mm=2.5,
            ond_mm=1.2
        )
        assert measurement.image_stem == "test_image"
        assert measurement.status == "meas_ok"
        assert measurement.onsd_mm == 2.5
        assert measurement.ond_mm == 1.2
    
    def test_measurement_as_dict(self):
        measurement = Measurement(
            image_stem="test",
            onsd_mm=2.5,
            raw={"extra_field": "value"}
        )
        result = measurement.as_dict()
        assert result["image_stem"] == "test"
        assert result["onsd_mm"] == 2.5
        assert result["extra_field"] == "value"


class TestEyeMeasurements:
    def test_average_onsd_mm(self, sample_measurements):
        eye_measurements = EyeMeasurements(measurements=sample_measurements)
        expected_avg = (2.37 + 2.19) / 2
        assert eye_measurements.average_onsd_mm == pytest.approx(expected_avg, 0.01)
    
    def test_average_onsd_mm_with_none(self):
        measurements = [
            Measurement(onsd_mm=2.5),
            Measurement(onsd_mm=None),
            Measurement(onsd_mm=3.0)
        ]
        eye_measurements = EyeMeasurements(measurements=measurements)
        assert eye_measurements.average_onsd_mm == pytest.approx(2.75, 0.01)
    
    def test_average_onsd_mm_all_none(self):
        measurements = [Measurement(onsd_mm=None) for _ in range(3)]
        eye_measurements = EyeMeasurements(measurements=measurements)
        assert eye_measurements.average_onsd_mm is None


class TestPatientReport:
    def test_patient_report_creation(self, sample_patient_report):
        assert sample_patient_report.patient_id == "TEST001"
        assert len(sample_patient_report.right_eye.measurements) == 3
        assert len(sample_patient_report.left_eye.measurements) == 3
    
    def test_all_measurements(self, sample_patient_report):
        all_measurements = sample_patient_report.all_measurements
        assert len(all_measurements) == 6
        assert all_measurements[0].onsd_mm == 2.37  # First right eye
        assert all_measurements[3].onsd_mm == 4.92  # First left eye
    
    def test_onsd_values(self, sample_patient_report):
        onsd_values = sample_patient_report.onsd_values
        expected = [2.37, 2.19, 4.92, 4.92, 4.92, 2.31]
        assert onsd_values == expected
    
    def test_capture_times(self):
        measurements = [
            Measurement(time="12:00:00"),
            Measurement(time=None),
            Measurement(time="12:01:00")
        ]
        right_eye = EyeMeasurements(measurements=measurements)
        left_eye = EyeMeasurements(measurements=measurements)
        report = PatientReport(patient_id="TEST", right_eye=right_eye, left_eye=left_eye)
        
        capture_times = report.capture_times
        assert capture_times == ["12:00:00", "—", "12:01:00", "12:00:00", "—", "12:01:00"]