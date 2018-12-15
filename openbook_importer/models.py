from django.db import models

class Posts(models.Model):
    timestamp = models.IntegerField()
    title = models.TextField()
    post = models.TextField()

    def __str__(self):
        return self.title
