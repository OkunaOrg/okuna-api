from sys import exit
from logging import getLogger

from django.conf import settings
from django.core.management.base import BaseCommand

from openbook_common.utils.rq_helpers import RQStats
from openbook_common.helpers import send_alert_to_channel

from openbook.settings import RQ_QUEUES, FAILED_JOB_THRESHOLD
from openbook.settings import ACTIVE_JOB_THRESHOLD, ACTIVE_WORKER_THRESHOLD


logger = getLogger(__name__)


class Command(BaseCommand):
    help = 'Check worker health'

    def verify_worker_health(self):
        # iterate through all configured queues

        env = settings.ENVIRONMENT

        for queue in RQ_QUEUES.keys():

            rq_stats = RQStats(queue)

            active_job_count = rq_stats.get_active_job_count()

            if active_job_count >= ACTIVE_JOB_THRESHOLD:
                send_alert_to_channel(
                        f"*UH-OH: we have way too many active jobs "
                        f"in {env}:{queue} right now: {active_job_count}!!*"
                                      )
                print(f"{queue} has too many jobs {active_job_count}")
                self.retval += 1

            active_worker_count = rq_stats.get_active_worker_count()

            if active_worker_count >= ACTIVE_WORKER_THRESHOLD:
                send_alert_to_channel(f"*Hmm, we are not supposed to have "
                                      f"{active_worker_count} workers in "
                                      f"{env}:{queue}*")
                print(f"{queue} has too many workers {active_worker_count}")

                self.retval += 1

    def handle(self, *args, **options):

        self.retval = 1

        try:
            self.verify_worker_health()

        except Exception as e:
            exception = str(e)
            send_alert_to_channel(
                               f"worker_health_check failed with {exception}"
                            )

            raise e

        # the return code will be equal to the amount of threshold
        # violation
        exit(self.retval)
