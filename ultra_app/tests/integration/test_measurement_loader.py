import pytest
import tempfile
import csv
import os
from ultra_app.interface_adapters.measurement_loader import MeasurementLoader
from ultra_app.domain.entities import Measurement


class TestMeasurementLoaderIntegration:
    def test_load_measurements_from_real_csv(self):
        # Create a temporary CSV file with real data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_stem', 'status', 'ONDpx', 'ONSDpx', 'ONDmm', 'ONSDmm', 'depthMM', 'latency_s'])
            writer.writerow(['01_16', 'meas_ok', '40', '79', '1.2', '2.37', '0.54', '0.76'])
            writer.writerow(['01_17', 'meas_ok', '27', '73', '0.81', '2.19', '0.51', '0.745'])
            csv_path = f.name
        
        try:
            loader = MeasurementLoader(csv_path)
            measurements = loader.load_measurements()
            
            assert len(measurements) == 2
            assert measurements[0].image_stem == '01_16'
            assert measurements[0].onsd_mm == 2.37
            assert measurements[0].ond_mm == 1.2
            assert measurements[1].image_stem == '01_17'
            assert measurements[1].onsd_mm == 2.19
        
        finally:
            os.unlink(csv_path)
    
    def test_load_patient_report_integration(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['image_stem', 'ONSDmm', 'ONDmm'])
            writer.writerow(['01_16', '2.37', '1.2'])
            writer.writerow(['01_17', '2.19', '0.81'])
            writer.writerow(['01_18', '4.92', '1.98'])
            writer.writerow(['01_19', '4.92', '1.98'])
            writer.writerow(['01_20', '4.92', '1.98'])
            writer.writerow(['01_21', '2.31', '0.03'])
            csv_path = f.name
        
        try:
            loader = MeasurementLoader(csv_path)
            report = loader.load_patient_report("TEST001")
            
            assert report.patient_id == "TEST001"
            assert len(report.right_eye.measurements) == 3
            assert len(report.left_eye.measurements) == 3
            assert report.right_eye.average_onsd_mm == pytest.approx((2.37 + 2.19 + 4.92) / 3, 0.01)
            assert report.left_eye.average_onsd_mm == pytest.approx((4.92 + 4.92 + 2.31) / 3, 0.01)
        
        finally:
            os.unlink(csv_path)