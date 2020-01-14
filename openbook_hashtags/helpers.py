import uuid
from os.path import splitext


def upload_to_hashtags_directory(hashtag, filename):
    extension = splitext(filename)[1].lower()
    new_filename = str(uuid.uuid4()) + extension

    path = 'hashtags/%(hashtag_name)s/' % {
        'hashtag_name': hashtag.name}

    return '%(path)s%(new_filename)s' % {'path': path,
                                         'new_filename': new_filename, }
