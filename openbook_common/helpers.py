from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException
import re
from django.conf import settings
from django.urls import reverse
import urllib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urlextract import URLExtract


from openbook_common.utils.model_loaders import get_language_model
from openbook_translation import translation_strategy

# seed the language detector
DetectorFactory.seed = 0


def get_detected_language_code(text):
    try:
        detected_lang = translation_strategy.get_detected_language_code(text)
    except LangDetectException:
        detected_lang = None
    return detected_lang


def get_language_for_text(text):
    language_code = get_detected_language_code(text)
    Language = get_language_model()
    if language_code is not None and Language.objects.filter(code=language_code).exists():
        return Language.objects.get(code=language_code)

    return None


def get_supported_translation_language(language_code):
    Language = get_language_model()
    supported_translation_code = translation_strategy.get_supported_translation_language_code(language_code)

    return Language.objects.get(code=supported_translation_code)


def get_matched_urls_from_text(text):
    text = text.lower()
    extractor = URLExtract()
    results = [url for url in extractor.gen_urls(text)]
    return results


def make_proxy_image_url(image_url):
    relative_url = reverse('proxy', kwargs={
        'url': image_url
    })
    proxy_image_url = settings.PROXY_HOST + relative_url

    return proxy_image_url


def is_url_allowed_in_whitelist_domains(url, allowed_domains):
    domain = get_domain_from_link(url)
    is_matched = False
    domain_parts = domain.split('.')
    length = len(domain_parts)
    while length >= 2:
        if domain in allowed_domains:
            is_matched = True
            break
        domain_parts.pop(0)
        domain = '.'.join(domain_parts)
        length = len(domain_parts)

    return is_matched


def get_domain_from_link(url):
    """
    Returns the domain part from a full url without the scheme
    """
    if not urlparse(url).scheme:
        url = 'https://' + url
    parsed_uri = urlparse(url)
    result = '{uri.netloc}'.format(uri=parsed_uri)
    return result.lower()


def _get_domain_full_url_from_link(url):
    """
    Returns the domain with scheme
    """
    parsed_uri = urlparse(url)
    result = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    return result.lower()


def get_favicon_url_from_link(url):
    if not urlparse(url).scheme:
        url = 'https://' + url

    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, features='html.parser')
    favicon_link = soup.find("link", rel="icon")
    if not favicon_link:
        favicon_link = soup.find("link", rel="shortcut icon")

    if favicon_link['href'][0] == '/':
        favicon_link = _get_domain_full_url_from_link(url) + favicon_link['href']
    else:
        favicon_link = favicon_link['href']

    return favicon_link


def get_sanitised_url_for_link(url):
    """
    Adds the url scheme if not present and converts urls to lowercase to normalise
    what we store in the model
    """
    if not urlparse(url).scheme:
        url = 'https://' + url

    return url.lower()
