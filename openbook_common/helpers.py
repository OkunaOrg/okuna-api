from langdetect import DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from django.conf import settings
import urllib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urlextract import URLExtract
from webpreview import web_preview

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


def extract_urls_from_string(text):
    """
    Returns all the raw extracted urls as a list
    If a URL has a scheme, it ensures that it is http/s
    URLs like www. are sanitised in the normalise_url
    """
    text = text.lower()
    extractor = URLExtract()
    results = [url for url in extractor.gen_urls(text)]
    for url in results:
        scheme = urlparse(url).scheme
        if scheme and scheme != 'https' and scheme != 'http':
            results.remove(url)

    return results


def make_proxy_image_url(image_url):
    proxy_image_url = settings.PROXY_URL + image_url

    return proxy_image_url


def get_url_domain(url):
    """
    Returns the domain from a full url without the scheme
    """
    if not urlparse(url).scheme:
        url = 'https://' + url
    parsed_uri = urlparse(url)
    result = '{uri.netloc}'.format(uri=parsed_uri)
    return result.lower()


def get_domain_with_protocol_from_url(url):
    parsed_uri = urlparse(url)
    result = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    return result.lower()


def get_favicon_url_from_url(url):
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, features='html.parser')
    favicon_link = soup.find("link", rel="icon")
    if not favicon_link:
        favicon_link = soup.find("link", rel="shortcut icon")

    if favicon_link['href'][0] == '/':
        favicon_link = get_domain_with_protocol_from_url(url) + favicon_link['href']
    else:
        favicon_link = favicon_link['href']

    return favicon_link


def normalise_url(url):
    if not urlparse(url).scheme:
        url = 'https://' + url

    return url.lower()


def get_url_metadata(preview_link):
    title, description, image_url = web_preview(preview_link, parser='html.parser')
    favicon_url = get_favicon_url_from_url(preview_link)
    domain_url = get_url_domain(preview_link)
    if image_url is not None:
        image_url = make_proxy_image_url(image_url)
    if favicon_url is not None:
        favicon_url = make_proxy_image_url(favicon_url)

    return {
        'title': title,
        'description': description,
        'image_url': image_url,
        'favicon_url': favicon_url,
        'domain_url': domain_url
    }
