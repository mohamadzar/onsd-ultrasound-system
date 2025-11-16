import pytest
import numpy as np
from ultra_app.domain.policies import SixImagesPolicy
from ultra_app.domain.entities import OperationState


class TestSixImagesPolicy:
    def test_initial_order(self):
        policy = SixImagesPolicy()
        order = policy.initial_order()
        
        assert len(order) == 6
        
        # Check right eye slots
        for i in range(3):
            assert order[i].eye == "Right"
            assert order[i].index_in_eye == i + 1
        
        # Check left eye slots
        for i in range(3, 6):
            assert order[i].eye == "Left"
            assert order[i].index_in_eye == i - 2
    
    def test_store_image_right_eye(self, sample_operation_state):
        policy = SixImagesPolicy()
        state = sample_operation_state
        processed_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # First slot is Right eye
        policy.store_image(state, processed_image)
        
        assert len(state.images_right) == 1
        assert len(state.images_left) == 0
        assert state.cursor == 1
        assert np.array_equal(state.images_right[0], processed_image)
    
    def test_store_image_left_eye(self, sample_operation_state):
        policy = SixImagesPolicy()
        state = sample_operation_state
        processed_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Move to left eye slots
        state.cursor = 3
        
        policy.store_image(state, processed_image)
        
        assert len(state.images_right) == 0
        assert len(state.images_left) == 1
        assert state.cursor == 4
        assert np.array_equal(state.images_left[0], processed_image)