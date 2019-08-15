import uuid
from os.path import splitext


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
