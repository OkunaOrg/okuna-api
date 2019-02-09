from django.db import models
from django.utils import timezone

from openbook_auth.models import User
from openbook_posts.models import Post


class Import(models.Model):

    created = models.DateTimeField(editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='imports', null=True)

    @classmethod
    def create_import(cls, user):
        imported = Import.objects.create(user=user)

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


class ImportedFriend(models.Model):

    # check if both uid fields are null, delete row
    friend_hash = models.CharField(max_length=64, unique=True)
    user1 = models.ForeignKey(User, on_delete=models.SET_NULL,
                              related_name='imported_friends',
                              null=True)
    user2 = models.ForeignKey(User, on_delete=models.SET_NULL,
                              related_name='connected_friend',
                              null=True)

    @classmethod
    def find_friend(cls, friend_hash, user):

        friend = ImportedFriend.objects.filter(friend_hash=friend_hash)

        if friend.exists():
            friend = friend[0]

            if friend.user1_id == user.pk and friend.user2_id:
                return True

            elif friend.user2_id == user.pk and friend.user1_id:
                return True

            elif friend.user1_id == user.pk and not friend.user2_id:
                return True

            elif friend.user2_id == user.pk and not friend.user1_id:
                return True

            elif not friend.user1_id and friend.user2_id != user.pk:
                friend.user1 = user
                friend.save()

                return True

            elif not friend.user2_id and friend.user1_id != user.pk:
                friend.user2 = user
                friend.save()

                return True

            else:
                return False

    @classmethod
    def create_imported_friend(cls, friend_hash, user1):
        imported_friend = ImportedFriend.objects.create(
                                friend_hash=friend_hash,
                                user1=user1)

        return imported_friend
