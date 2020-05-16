from django.db import models

# Create your models here.
from openbook_auth.models import User


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follows')
    followed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers', null=False)

    class Meta:
        unique_together = ('user', 'followed_user',)
        indexes = [
            models.Index(fields=['followed_user', 'user']),
        ]

    @classmethod
    def create_follow(cls, user_id, followed_user_id, lists_ids=None):
        follow = Follow.objects.create(user_id=user_id, followed_user_id=followed_user_id)

        if lists_ids:
            follow.lists.add(*lists_ids)

        return follow


class FollowRequest(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_follow_requests')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_follow_requests', null=False)

    class Meta:
        unique_together = ('creator', 'target_user',)
        indexes = [
            models.Index(fields=['creator', 'target_user']),
        ]

    @classmethod
    def create_follow_request(cls, creator_id, target_user_id):
        follow_request = FollowRequest.objects.create(creator_id=creator_id, target_user_id=target_user_id)

        return follow_request

    @classmethod
    def delete_follow_request(cls, creator_id, target_user_id):
        return FollowRequest.objects.filter(creator_id=creator_id, target_user_id=target_user_id).delete()
