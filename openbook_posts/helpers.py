import uuid
import urllib
from urllib.parse import urlparse
from os.path import splitext
from bs4 import BeautifulSoup


def upload_to_post_image_directory(post_image, filename):
    post = post_image.post
    return _upload_to_post_directory_directory(post=post, filename=filename)


def upload_to_post_video_directory(post_video, filename):
    post = post_video.post
    return _upload_to_post_directory_directory(post=post, filename=filename)


def _upload_to_post_directory_directory(post, filename):
    extension = splitext(filename)[1].lower()
    new_filename = str(uuid.uuid4()) + extension

    path = 'posts/%(post_uuid)s/' % {
        'post_uuid': str(post.uuid)}

    return '%(path)s%(new_filename)s' % {'path': path,
                                         'new_filename': new_filename, }


def get_favicon_url_from_link(url):
    if not urlparse(url).scheme:
        url = 'https://' + url

    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page, features='html.parser')
    favicon_link = soup.find("link", rel="icon")
    if not favicon_link:
        favicon_link = soup.find("link", rel="shortcut icon")

    return favicon_link['href']
