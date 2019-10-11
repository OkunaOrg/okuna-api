import django_rq
from django_rq.utils import get_statistics, FailedJobRegistry


class RQStats():

    def __init__(self, queue):

        self.stats = get_statistics()
        self.queue_name = queue

    def get_active_worker_count(self):

        queue = self._get_queue_by_name(self.queue_name)
        workers = queue.get('workers', 0)

        return workers

    def get_active_job_count(self):

        queue = self._get_queue_by_name(self.queue_name)
        jobs = queue.get('jobs', 0)

        return jobs

    def get_failed_job_count(self):

        queue = self._get_queue_by_name(self.queue_name)
        failed_jobs = queue.get('failed_jobs', 0)

        return failed_jobs

    def _get_queue_by_name(self, name):

        queues = self.stats.get('queues')

        for q in queues:
            if q['name'] == name:
                return q

        raise ValueError(f"queue {name} not found")


class FailedRQJobs():

    def __init__(self, queue):

        self.queue = django_rq.get_queue(queue)
        self.connection = django_rq.get_connection()
        self.failed_job_registry = FailedJobRegistry(self.queue,
                                                     self.connection)

    def delete_all_failed_jobs_from_queue(self):

        failed_job_ids = self.failed_job_registry.get_job_ids()

        for failed_job in failed_job_ids:
            job = self.queue.fetch_job(failed_job)

            job.delete()
