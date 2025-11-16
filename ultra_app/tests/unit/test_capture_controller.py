import pytest
import numpy as np
from unittest.mock import Mock
# re-exportiert alle Fixtures aus der Eltern-conftest
from ..conftest import *  # noqa

from ultra_app.domain.ports import ProcessorGateway
from ultra_app.use_cases.capture_controller import CaptureController
from ultra_app.domain.policies import SixImagesPolicy


class TestCaptureController:
    def test_initialization(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        assert controller.processor == mock_processor
        assert controller.policy == policy
        assert not controller.state.is_complete()
    
    def test_progress_vector(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        current, total = controller.progress_vector()
        assert current == 1
        assert total == 6
        
        # Advance cursor
        controller.state.cursor = 3
        current, total = controller.progress_vector()
        assert current == 4
        assert total == 6
    
    def test_is_complete(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        assert not controller.is_complete()
        
        controller.state.cursor = 6
        assert controller.is_complete()
    
    def test_next_expected_label(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        # First should be Right #1
        assert controller.next_expected_label() == "Right #1"
        
        # Advance to left eye
        controller.state.cursor = 3
        assert controller.next_expected_label() == "Left #1"
        
        # When complete
        controller.state.cursor = 6
        assert controller.next_expected_label() == "Completed"
    
    def test_process_only(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        input_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_processor.process.return_value = processed_frame
        
        result = controller.process_only(input_frame)
        
        mock_processor.process.assert_called_once_with(input_frame)
        assert np.array_equal(result, processed_frame)
        # State should not be modified
        assert controller.state.cursor == 0
    
    def test_capture(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        input_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_processor.process.return_value = processed_frame
        
        controller.capture(input_frame)
        
        mock_processor.process.assert_called_once_with(input_frame)
        assert controller.state.cursor == 1
        assert len(controller.state.images_right) == 1
        assert np.array_equal(controller.state.images_right[0], processed_frame)
    
    def test_capture_when_complete(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        controller.state.cursor = 6  # Mark as complete
        
        input_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        with pytest.raises(RuntimeError, match="All 6 images already captured"):
            controller.capture(input_frame)
    
    def test_undo(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        # Capture one image
        input_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_processor.process.return_value = input_frame
        controller.capture(input_frame)
        
        assert controller.state.cursor == 1
        assert len(controller.state.images_right) == 1
        
        # Undo
        controller.undo()
        
        assert controller.state.cursor == 0
        assert len(controller.state.images_right) == 0
    
    def test_undo_at_start(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        # Should not crash when undoing at start
        controller.undo()
        assert controller.state.cursor == 0
    
    def test_reset(self, mock_processor):
        policy = SixImagesPolicy()
        controller = CaptureController(mock_processor, policy)
        
        # Capture some images
        input_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_processor.process.return_value = input_frame
        controller.capture(input_frame)
        controller.capture(input_frame)
        
        assert controller.state.cursor == 2
        assert len(controller.state.images_right) == 2
        
        # Reset
        controller.reset()
        
        assert controller.state.cursor == 0
        assert len(controller.state.images_right) == 0
        assert len(controller.state.images_left) == 0