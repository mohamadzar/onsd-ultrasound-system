import pytest
import tempfile
import os
import numpy as np
from ultra_app.interface_adapters.report_writer import ReportWriter
from ultra_app.domain.entities import ReportData, PatientReport, EyeMeasurements, Measurement


class TestReportWriterIntegration:
    def test_report_generation_with_real_data(self):
        # Create sample measurements
        measurements = [
            Measurement(
                image_stem=f"0{i+1}_{16+i}",
                status="meas_ok",
                ond_px=[40, 27, 66, 66, 66, 1][i],
                onsd_px=[79, 73, 164, 164, 164, 77][i],
                ond_mm=[1.2, 0.81, 1.98, 1.98, 1.98, 0.03][i],
                onsd_mm=[2.37, 2.19, 4.92, 4.92, 4.92, 2.31][i],
                depth_mm=0.54,
                latency_s=0.75,
                time=f"12:0{i}:00"
            ) for i in range(6)
        ]
        
        right_eye = EyeMeasurements(measurements=measurements[:3])
        left_eye = EyeMeasurements(measurements=measurements[3:])
        patient_report = PatientReport(
            patient_id="INTEGRATION_TEST",
            right_eye=right_eye,
            left_eye=left_eye
        )
        
        # Create sample images
        right_images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]
        left_images = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(3)]

        writer = ReportWriter(threshold_mm=6.0)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Fix: Use the correct method signature
            png_path, pdf_path = writer.save_report(
                images_right=right_images,
                images_left=left_images,
                out_dir=temp_dir,
                onsd_values=[m.onsd_mm for m in measurements],
                capture_times=[m.time for m in measurements],
                patient_id="INTEGRATION_TEST",
                ond_values=[m.ond_mm for m in measurements],
                onsd_px_values=[m.onsd_px for m in measurements],
                ond_px_values=[m.ond_px for m in measurements],
                depth_values=[m.depth_mm for m in measurements],
                latency_values=[m.latency_s for m in measurements],
                status_values=[m.status for m in measurements]
            )
            
            # Verify files were created
            assert os.path.exists(png_path)
            assert os.path.exists(pdf_path)
            assert png_path.endswith('.png')
            assert pdf_path.endswith('.pdf')
            
            # Verify file sizes are reasonable
            assert os.path.getsize(png_path) > 1000  # At least 1KB
            assert os.path.getsize(pdf_path) > 1000  # At least 1KB