# ultra_app/tests/unit/test_export_report.py
import pytest
import tempfile
import numpy as np
from unittest.mock import Mock, patch
from ultra_app.use_cases.export_report import ExportReport
from ultra_app.domain.entities import OperationState, Measurement


class TestExportReport:
    def test_export_success(self, mock_report_writer, sample_operation_state):
        exporter = ExportReport(mock_report_writer)
        state = sample_operation_state
        
        # Mark as complete and add some images
        state.cursor = 6
        state.images_right = [Mock() for _ in range(3)]
        state.images_left = [Mock() for _ in range(3)]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            png_path, pdf_path = exporter.export(state, temp_dir)
            
            mock_report_writer.save_report.assert_called_once()
            assert png_path == "test_report.png"
            assert pdf_path == "test_report.pdf"
    
    def test_export_incomplete_state(self, mock_report_writer, sample_operation_state):
        exporter = ExportReport(mock_report_writer)
        state = sample_operation_state  # Not complete
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(RuntimeError, match="Capture all 6 images before exporting"):
                exporter.export(state, temp_dir)
    
    @patch('ultra_app.use_cases.export_report.MeasurementLoader')
    def test_export_with_csv_measurements_success(self, mock_loader_class, mock_report_writer):
        # Setup mocks
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader
        
        # Create proper Measurement objects
        mock_measurements = [
            Measurement(
                image_stem="01_16",
                onsd_mm=2.37,
                ond_mm=1.2,
                time="12:00:00",
                status="meas_ok",
                onsd_px=79.0,
                ond_px=40.0,
                depth_mm=0.54,
                latency_s=0.76
            ),
            Measurement(
                image_stem="01_17",
                onsd_mm=2.19,
                ond_mm=0.81,
                time="12:01:00",
                status="meas_ok",
                onsd_px=73.0,
                ond_px=27.0,
                depth_mm=0.51,
                latency_s=0.745
            ),
        ]
        
        # Mock the load_measurements method
        mock_loader.load_measurements.return_value = mock_measurements

        exporter = ExportReport(mock_report_writer)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test captured images
            captured_images_right = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]
            captured_images_left = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]

            png_path, pdf_path = exporter.export_with_csv_measurements(
                images_right=captured_images_right,
                images_left=captured_images_left,
                measurements_csv="dummy.csv",
                out_dir=temp_dir,
                patient_id="TEST001"
            )
            
            mock_report_writer.save_report.assert_called_once()
            assert png_path == "test_report.png"
            assert pdf_path == "test_report.pdf"
    
    @patch('ultra_app.use_cases.export_report.MeasurementLoader')
    def test_export_with_csv_measurements_empty_csv(self, mock_loader_class, mock_report_writer):
        """Test that empty CSV files are handled gracefully"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader
        
        # Mock empty measurements
        mock_loader.load_measurements.return_value = []

        exporter = ExportReport(mock_report_writer)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test captured images
            captured_images_right = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]
            captured_images_left = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]

            png_path, pdf_path = exporter.export_with_csv_measurements(
                images_right=captured_images_right,
                images_left=captured_images_left,
                measurements_csv="empty.csv",
                out_dir=temp_dir,
                patient_id="TEST001"
            )
            
            # Should still call save_report but with None values
            mock_report_writer.save_report.assert_called_once()
            assert png_path == "test_report.png"
            assert pdf_path == "test_report.pdf"