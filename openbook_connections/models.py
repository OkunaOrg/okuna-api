from django.db import models

# Create your models here.
from openbook_auth.models import User
from openbook_circles.models import Circle
from django.utils.translation import ugettext_lazy as _


class Connection(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='connections')
    circle = models.ForeignKey(Circle, on_delete=models.CASCADE, related_name='connections')
    target_connection = models.OneToOneField('self', on_delete=models.CASCADE)
    following = models.BooleanField(_('following'), default=True, blank=False, null=False)
