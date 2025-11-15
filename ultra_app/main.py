# ultra_app/main.py

from ultra_app.interface_adapters.processor_ultra import ULTRAProcessor
from ultra_app.interface_adapters.report_writer import ReportWriter
from ultra_app.interface_adapters.presenter import OperationPresenter
from ultra_app.interface_adapters.camera_opencv import OpenCVCamera

from ultra_app.domain.policies import SixImagesPolicy

from ultra_app.use_cases.capture_controller import CaptureController
from ultra_app.use_cases.export_report import ExportReport

from ultra_app.frameworks.gui_qt import run_gui
import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    processor = ULTRAProcessor()
    policy = SixImagesPolicy()
    controller = CaptureController(processor, policy)

    writer = ReportWriter()
    exporter = ExportReport(writer)

    presenter = OperationPresenter()
    camera = OpenCVCamera(device_index=0, width=1280, height=720)

    run_gui(
        controller=controller,
        exporter=exporter,
        presenter=presenter,
        camera=camera,
    )


if __name__ == "__main__":
    main()
