from django.db import models
from django.utils import timezone

from openbook_posts.models import Post


class Import(models.Model):

    created = models.DateTimeField(editable=False)

    @classmethod
    def create_import(cls):
        imported = Import.objects.create()

        return imported

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id and not self.created:
            self.created = timezone.now()

        return super(Import, self).save(*args, **kwargs)


class ImportedPost(models.Model):

    data_import = models.ForeignKey(Import, on_delete=models.CASCADE,
                                    related_name='imported_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE)

    @classmethod
    def create_imported_post(cls, post, data_import):
        imported_post = ImportedPost.objects.create(post=post,
                                                    data_import=data_import)

        return imported_post
