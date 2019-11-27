from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.
from openbook_auth.models import User
from django.utils.translation import ugettext_lazy as _

from openbook_categories.models import Category
from openbook_common.utils.helpers import generate_random_hex_color
from openbook_common.validators import hex_color_validator
from openbook_communities.models import Community

