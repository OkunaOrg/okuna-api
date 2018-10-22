from django.db import models

# Create your models here.
from openbook_auth.models import User


from openbook_lists.models import List


class Follow(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='follows')
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name='follows')
    followed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
