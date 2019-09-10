from rest_framework.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _

from openbook_common.helpers import extract_urls_from_string
from openbook_common.utils.model_loaders import get_proxy_whitelist_domain_model


# This check is used on nginx auth, doesn't support 400
def check_url_can_be_proxied(url):
    urls = extract_urls_from_string(url)

    if not urls:
        raise PermissionDenied(
            _('No valid URL given'),
        )

    ProxyWhitelistDomain = get_proxy_whitelist_domain_model()
    if not ProxyWhitelistDomain.is_url_domain_whitelisted(url):
        raise PermissionDenied(
            _('Url domain is not proxy whitelisted'),
        )
