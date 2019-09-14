from django_rq.decorators import job

from openbook_common.utils.rq_helpers import RQStats
from openbook_common.helpers import send_alert_to_channel

from openbook.settings import FAILED_JOB_TRESHOLD
from openbook.settings import ACTIVE_JOB_TRESHOLD, ACTIVE_WORKER_TRESHOLD


@job
def verify_failed_job_threshold():

    rq_stats = RQStats()
    failed_job_count = rq_stats.get_failed_job_count()

    if failed_job_count >= FAILED_JOB_TRESHOLD:
        send_alert_to_channel(f"*OH NOES: we haz too many failed jobs "
                              f"({failed_job_count})!!*")


@job
def verify_active_job_threshold():

    rq_stats = RQStats()
    active_job_count = rq_stats.get_active_job_count()

    if active_job_count >= ACTIVE_JOB_TRESHOLD:
        send_alert_to_channel(f"*UH-OH: we have way too many active jobs right "
                              f"now: {active_job_count}!!*")


@job
def verify_active_worker_threshold():

    rq_stats = RQStats()
    active_worker_count = rq_stats.get_active_worker_count()

    if active_worker_count >= ACTIVE_WORKER_TRESHOLD:
        send_alert_to_channel(f"*Hmm, we are not supposed to have "
                              f"{active_worker_count} workers*")
