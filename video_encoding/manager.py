from django.db.models import Manager
from django.db.models.query import QuerySet


class FormatQuerySet(QuerySet):
    def in_progress(self):
        return self.filter(progress__lt=100)

    def complete(self):
        return self.filter(progress=100)


class FormatManager(Manager.from_queryset(FormatQuerySet)):
    use_for_related_fields = True
