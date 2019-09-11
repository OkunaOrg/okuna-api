import tempfile


def get_fieldfile_local_path(fieldfile):
    storage = fieldfile.storage
    local_temp_file = None

    try:
        # Try to access with path
        storage_local_path = storage.path(fieldfile.path)
    except (NotImplementedError, AttributeError):
        # Storage doesnt support absolute paths, download file to a temp local dir
        storage_file = storage.open(fieldfile.name, 'r')
        local_temp_file = tempfile.NamedTemporaryFile(delete=False)
        local_temp_file.write(storage_file.read())
        local_temp_file.seek(0)

        storage_local_path = local_temp_file.name

    return storage_local_path, local_temp_file
