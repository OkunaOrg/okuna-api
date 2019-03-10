import uuid
from os.path import splitext


def upload_to_user_avatar_directory(user_profile, filename):
    user = user_profile.user
    return _upload_to_user_directory(user=user, filename=filename)


def upload_to_user_cover_directory(user_profile, filename):
    user = user_profile.user
    return _upload_to_user_directory(user=user, filename=filename)


def _upload_to_user_directory(user, filename):
    extension = splitext(filename)[1].lower()
    new_filename = str(uuid.uuid4()) + extension

    path = 'users/%(user_uuid)s/' % {
        'user_uuid': str(user.id)}

    return '%(path)s%(new_filename)s' % {'path': path,
                                         'new_filename': new_filename, }
