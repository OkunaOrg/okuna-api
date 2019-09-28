# Create your models here.
# Create your models here.
from urllib.parse import urlparse

from django.conf import settings
from django.db import models
from django.db.models import QuerySet, Q, Count
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# Create your views here.
from openbook.settings import COLOR_ATTR_MAX_LENGTH
from openbook_common.validators import hex_color_validator
import tldextract


class EmojiGroup(models.Model):
    keyword = models.CharField(_('keyword'), max_length=32, blank=False, null=False)
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator], unique=False)
    order = models.IntegerField(unique=False, default=100)
    created = models.DateTimeField(editable=False)
    is_reaction_group = models.BooleanField(_('is reaction group'), default=False)

    def __str__(self):
        return 'EmojiGroup: ' + self.keyword

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(EmojiGroup, self).save(*args, **kwargs)

    def has_emoji_with_id(self, emoji_id):
        return self.emojis.filter(pk=emoji_id).exists()


class Emoji(models.Model):
    group = models.ForeignKey(EmojiGroup, on_delete=models.CASCADE, related_name='emojis', null=True)
    keyword = models.CharField(_('keyword'), max_length=16, blank=False, null=False)
    # Hex colour. #FFFFFF
    color = models.CharField(_('color'), max_length=COLOR_ATTR_MAX_LENGTH, blank=False, null=False,
                             validators=[hex_color_validator], unique=False)
    image = models.ImageField(_('image'), blank=False, null=False)
    created = models.DateTimeField(editable=False)
    order = models.IntegerField(unique=False, default=100)

    @classmethod
    def get_emoji_counts_for_post_comment_with_id(cls, post_comment_id, emoji_id=None, reactor_id=None):
        emoji_query = Q(post_comment_reactions__post_comment_id=post_comment_id, )

        if emoji_id:
            emoji_query.add(Q(post_comment_reactions__emoji_id=emoji_id), Q.AND)

        if reactor_id:
            emoji_query.add(Q(post_comment_reactions__reactor_id=reactor_id), Q.AND)

        emojis = Emoji.objects.filter(emoji_query).annotate(Count('post_comment_reactions')).distinct().order_by(
            '-post_comment_reactions__count').cache().all()

        return [{'emoji': emoji, 'count': emoji.post_comment_reactions__count} for emoji in emojis]

    @classmethod
    def get_emoji_counts_for_post_with_id(cls, post_id, emoji_id=None, reactor_id=None):
        emoji_query = Q(post_reactions__post_id=post_id, )

        if emoji_id:
            emoji_query.add(Q(post_reactions__emoji_id=emoji_id), Q.AND)

        if reactor_id:
            emoji_query.add(Q(post_reactions__reactor_id=reactor_id), Q.AND)

        emojis = Emoji.objects.filter(emoji_query).annotate(Count('post_reactions')).distinct().order_by(
            '-post_reactions__count').cache().all()

        return [{'emoji': emoji, 'count': emoji.post_reactions__count} for emoji in emojis]

    def __str__(self):
        return 'Emoji: ' + self.keyword

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Emoji, self).save(*args, **kwargs)


class Badge(models.Model):
    keyword = models.CharField(max_length=16, blank=False, null=False, unique=True)
    keyword_description = models.CharField(_('keyword_description'), max_length=64, blank=True, null=True, unique=True)
    created = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Badge, self).save(*args, **kwargs)


class Language(models.Model):
    code = models.CharField(_('code'), max_length=12, blank=False, null=False)
    name = models.CharField(_('name'), max_length=64, blank=False, null=False)
    created = models.DateTimeField(editable=False)

    def __str__(self):
        return 'Language: ' + self.code

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        return super(Language, self).save(*args, **kwargs)


class ProxyBlacklistedDomain(models.Model):
    domain = models.CharField(max_length=settings.PROXY_BLACKLIST_DOMAIN_MAX_LENGTH, unique=True)

    @classmethod
    def is_url_domain_blacklisted(cls, url):
        url = url.lower()

        if not urlparse(url).scheme:
            url = 'http://' + url

        # This uses a list of public suffixes
        tld_extract_result = tldextract.extract(url)

        # given test.blogspot.com

        # blogspot.com
        url_root_domain = '.'.join([tld_extract_result.domain, tld_extract_result.suffix])

        # test.blogspot.com
        url_full_domain = '.'.join([tld_extract_result.subdomain, tld_extract_result.domain, tld_extract_result.suffix])

        return cls.objects.filter(Q(domain=url_root_domain) | Q(domain=url_full_domain)).exists()
