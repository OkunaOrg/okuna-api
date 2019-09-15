from unittest.mock import patch

from django.test import TestCase

from openbook_common import jobs
from openbook_common.utils.rq_helpers import RQStats

from openbook.settings import ACTIVE_WORKER_THRESHOLD
from openbook.settings import ACTIVE_JOB_THRESHOLD, FAILED_JOB_THRESHOLD


class ThresholdAlertTestCases(TestCase):

    """Testing redis queue threshold and sending of alerts"""

    def test_failed_jobs_threshold_reached(self):
        """Test if going over the failed job threshold result in
           a call to send_alert_to_channel, should be called."""

        fail_count = FAILED_JOB_THRESHOLD + 10

        #  make get_failed_job_count return 40
        with patch.object(RQStats, 'get_failed_job_count',
                          return_value=fail_count):

            # patch the call to prevent an actual message from being sent
            with patch.object(jobs, 'send_alert_to_channel',
                              return_value=0) as _send_alert:
                jobs.verify_failed_job_threshold()

                _send_alert.assert_called()

    def test_active_worker_threshold_reached(self):
        """Test if 10 active workers calls send_alert_to_channel,
           should be called"""

        worker_count = ACTIVE_WORKER_THRESHOLD + 5

        with patch.object(RQStats, 'get_active_worker_count',
                          return_value=worker_count):

            with patch.object(jobs, 'send_alert_to_channel',
                              return_value=0) as _send_alert:
                jobs.verify_active_worker_threshold()

                _send_alert.assert_called()

    def test_active_job_threshold_reached(self):
        """Test if 55 active jobs calls send_alert_to_channel,
           should be called"""

        job_count = ACTIVE_JOB_THRESHOLD + 5

        with patch.object(RQStats, 'get_active_job_count',
                          return_value=job_count):

            with patch.object(jobs, 'send_alert_to_channel',
                              return_value=0) as _send_alert:
                jobs.verify_active_job_threshold()

                _send_alert.assert_called()

    def test_failed_job_threshold_not_reached(self):
        """Test if 10 failed jobs calls sends_alert_to_channel,
           should not be called"""

        fail_count = FAILED_JOB_THRESHOLD - 10

        with patch.object(RQStats, 'get_failed_job_count',
                          return_value=fail_count):

            with patch.object(jobs, 'send_alert_to_channel',
                              return_value=0) as _send_alert:
                jobs.verify_failed_job_threshold()

                _send_alert.assert_not_called()

    def test_active_worker_threshold_not_reached(self):
        """Test if 3 active workers calls send_alert_to_channel,
           should not be called"""

        worker_count = ACTIVE_WORKER_THRESHOLD - 2

        with patch.object(RQStats, 'get_active_worker_count',
                          return_value=worker_count):

            with patch.object(jobs, 'send_alert_to_channel',
                              return_value=0) as _send_alert:
                jobs.verify_active_worker_threshold()

                _send_alert.assert_not_called()

    def test_active_job_threshold_not_reached(self):
        """Test if 20 active jobs calls send_alert_to_channel,
           should not be called"""

        job_count = ACTIVE_JOB_THRESHOLD - 30

        with patch.object(RQStats, 'get_active_job_count',
                          return_value=job_count):

            with patch.object(jobs, 'send_alert_to_channel',
                              return_value=0) as _send_alert:
                jobs.verify_active_job_threshold()

                _send_alert.assert_not_called()
