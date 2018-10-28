from django.db import models

# Create your models here.
from openbook_auth.models import User

from openbook_lists.models import List


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follows')
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='follows', null=True)
    followed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', null=False)

    class Meta:
        unique_together = ('user', 'followed_user',)

    @classmethod
    def create_follow(cls, user_id, followed_user_id, **kwargs):
        return Follow.objects.create(user_id=user_id, followed_user_id=followed_user_id, **kwargs)
