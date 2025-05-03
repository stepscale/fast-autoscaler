import unittest
from unittest import mock
import time

from autoscaler.scaler import calculate_new_task_count, can_scale


class TestScaler(unittest.TestCase):
    """Tests for the core scaling logic."""

    def test_calculate_new_task_count_no_scaling(self):
        """Test that no scaling occurs when queue is within thresholds."""
        current_task_count = 10
        total_messages = 50  # Between scale up and scale down thresholds
        messages_per_task = 5
        total_messages_combined = 60

        new_task_count = calculate_new_task_count(
            current_task_count=current_task_count,
            total_messages=total_messages,
            messages_per_task=messages_per_task,
            total_messages_combined=total_messages_combined,
            min_tasks=1,
            max_tasks=100,
            scale_up_threshold=100,
            scale_down_threshold=10,
            tasks_per_message=0.01,
            max_scale_down_factor=0.5
        )

        self.assertEqual(new_task_count, current_task_count)

    def test_calculate_new_task_count_scale_up(self):
        """Test scaling up when queue exceeds threshold."""
        current_task_count = 10
        total_messages = 200  # Above scale up threshold
        messages_per_task = 20
        total_messages_combined = 220

        new_task_count = calculate_new_task_count(
            current_task_count=current_task_count,
            total_messages=total_messages,
            messages_per_task=messages_per_task,
            total_messages_combined=total_messages_combined,
            min_tasks=1,
            max_tasks=100,
            scale_up_threshold=100,
            scale_down_threshold=10,
            tasks_per_message=0.01,
            max_scale_down_factor=0.5
        )

        # Should add at least 2 tasks (200 * 0.01 = 2)
        self.assertGreater(new_task_count, current_task_count)
        self.assertEqual(new_task_count, 12)  # 10 + 2 = 12

    def test_calculate_new_task_count_scale_down(self):
        """Test scaling down when queue is below threshold."""
        current_task_count = 10
        total_messages = 5  # Below scale down threshold
        messages_per_task = 0.5
        total_messages_combined = 5

        new_task_count = calculate_new_task_count(
            current_task_count=current_task_count,
            total_messages=total_messages,
            messages_per_task=messages_per_task,
            total_messages_combined=total_messages_combined,
            min_tasks=1,
            max_tasks=100,
            scale_up_threshold=100,
            scale_down_threshold=10,
            tasks_per_message=0.01,
            max_scale_down_factor=0.5
        )

        # Should scale down but not more than 50% (max_scale_down_factor)
        self.assertLess(new_task_count, current_task_count)
        self.assertEqual(new_task_count, 5)  # min(max(1, 5*0.01=0), 10*0.5=5)

    def test_calculate_new_task_count_min_constraint(self):
        """Test that scaling respects the minimum task constraint."""
        current_task_count = 5
        total_messages = 1  # Very few messages
        messages_per_task = 0.2
        total_messages_combined = 1

        new_task_count = calculate_new_task_count(
            current_task_count=current_task_count,
            total_messages=total_messages,
            messages_per_task=messages_per_task,
            total_messages_combined=total_messages_combined,
            min_tasks=3,  # Minimum 3 tasks
            max_tasks=100,
            scale_up_threshold=100,
            scale_down_threshold=10,
            tasks_per_message=0.01,
            max_scale_down_factor=0.5
        )

        # Should not go below min_tasks (3)
        self.assertEqual(new_task_count, 3)

    def test_calculate_new_task_count_max_constraint(self):
        """Test that scaling respects the maximum task constraint."""
        current_task_count = 90
        total_messages = 5000  # Lots of messages
        messages_per_task = 55.55
        total_messages_combined = 5500

        new_task_count = calculate_new_task_count(
            current_task_count=current_task_count,
            total_messages=total_messages,
            messages_per_task=messages_per_task,
            total_messages_combined=total_messages_combined,
            min_tasks=1,
            max_tasks=100,  # Maximum 100 tasks
            scale_up_threshold=100,
            scale_down_threshold=10,
            tasks_per_message=0.01,
            max_scale_down_factor=0.5
        )

        # Should not exceed max_tasks (100)
        self.assertEqual(new_task_count, 100)

    @mock.patch('autoscaler.scaler.get_last_scaling_time')
    def test_can_scale_up_bypass_cooldown(self, mock_get_last_scaling_time):
        """Test that scale up always bypasses cooldown."""
        # Mock the get_last_scaling_time function to simulate cooldown period
        mock_get_last_scaling_time.return_value = (time.time() - 10, 1)  # 10 seconds ago, still in cooldown

        aws_wrapper = mock.MagicMock()

        # Scale up from 10 to 15 tasks
        result = can_scale(
            aws_wrapper=aws_wrapper,
            action_type='up',
            current_task_count=10,
            new_task_count=15,
            s3_config_bucket='test-bucket',
            ecs_cluster='test-cluster',
            service_name='test-service',
            scale_out_cooldown=60,  # 60 second cooldown
            scale_in_cooldown=60
        )

        # Should be able to scale up even during cooldown
        self.assertTrue(result)

    @mock.patch('autoscaler.scaler.get_last_scaling_time')
    def test_can_scale_down_respect_cooldown(self, mock_get_last_scaling_time):
        """Test that scale down respects cooldown period."""
        # Mock the get_last_scaling_time function to simulate cooldown period
        current_time = time.time()

        # When called with 'up', return a time far in the past
        # When called with 'down', return a recent time that's still in cooldown
        mock_get_last_scaling_time.side_effect = lambda aws, action, bucket, cluster, service: (
            (current_time - 3600, 1) if action == 'up' else (current_time - 10, 1)
        )

        aws_wrapper = mock.MagicMock()

        # Scale down from 10 to 5 tasks
        result = can_scale(
            aws_wrapper=aws_wrapper,
            action_type='down',
            current_task_count=10,
            new_task_count=5,
            s3_config_bucket='test-bucket',
            ecs_cluster='test-cluster',
            service_name='test-service',
            scale_out_cooldown=60,
            scale_in_cooldown=60  # 60 second cooldown
        )

        # Should not be able to scale down during cooldown
        self.assertFalse(result)

    @mock.patch('autoscaler.scaler.get_last_scaling_time')
    def test_can_scale_down_after_cooldown(self, mock_get_last_scaling_time):
        """Test that scale down is allowed after cooldown period."""
        current_time = time.time()

        # When called with 'up', return a time far in the past
        # When called with 'down', return a time after cooldown period
        mock_get_last_scaling_time.side_effect = lambda aws, action, bucket, cluster, service: (
            (current_time - 3600, 1) if action == 'up' else (current_time - 70, 1)
        )

        aws_wrapper = mock.MagicMock()

        # Scale down from 10 to 5 tasks
        result = can_scale(
            aws_wrapper=aws_wrapper,
            action_type='down',
            current_task_count=10,
            new_task_count=5,
            s3_config_bucket='test-bucket',
            ecs_cluster='test-cluster',
            service_name='test-service',
            scale_out_cooldown=60,
            scale_in_cooldown=60  # 60 second cooldown
        )

        # Should be able to scale down after cooldown period
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()