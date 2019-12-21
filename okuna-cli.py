import random
import time
import click
import subprocess
import colorlog
import logging
import os.path
from shutil import copyfile
import json
import atexit
import os, errno

import requests
from halo import Halo

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(name)s -> %(message)s'))

logger = colorlog.getLogger('🤖')
logger.addHandler(handler)

logger.setLevel(level=logging.DEBUG)

current_dir = os.path.dirname(__file__)

OKUNA_CLI_CONFIG_FILE = os.path.join(current_dir, '.okuna-cli.json')
OKUNA_CLI_CONFIG_FILE_TEMPLATE = os.path.join(current_dir, 'templates/.okuna-cli.json')

LOCAL_API_ENV_FILE = os.path.join(current_dir, '.env')
LOCAL_API_ENV_FILE_TEMPLATE = os.path.join(current_dir, 'templates/.env')

DOCKER_COMPOSE_ENV_FILE = os.path.join(current_dir, '.docker-compose.env')
DOCKER_COMPOSE_ENV_FILE_TEMPLATE = os.path.join(current_dir, 'templates/.docker-compose.env')

REQUIREMENTS_TXT_FILE = os.path.join(current_dir, 'requirements.txt')
DOCKER_API_IMAGE_REQUIREMENTS_TXT_FILE = os.path.join(current_dir, '.docker', 'api', 'requirements.txt')
DOCKER_WORKER_IMAGE_REQUIREMENTS_TXT_FILE = os.path.join(current_dir, '.docker', 'worker', 'requirements.txt')
DOCKER_SCHEDULER_IMAGE_REQUIREMENTS_TXT_FILE = os.path.join(current_dir, '.docker', 'scheduler', 'requirements.txt')
DOCKER_API_TEST_IMAGE_REQUIREMENTS_TXT_FILE = os.path.join(current_dir, '.docker', 'api-test', 'requirements.txt')

CONTEXT_SETTINGS = dict(
    default_map={}
)

random_generator = random.SystemRandom()


def _remove_file_silently(filename):
    try:
        os.remove(filename)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


def _get_random_string(length=12,
                       allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                     'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Return a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    return ''.join(random.choice(allowed_chars) for i in range(length))


def _get_django_secret_key():
    """
    Return a 50 character random string usable as a SECRET_KEY setting value.
    """
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    return _get_random_string(50, chars)


def _get_mysql_password():
    return _get_random_string(64)


def _get_redis_password():
    return _get_random_string(128)


def _copy_requirements_txt_to_docker_images_dir():
    copyfile(REQUIREMENTS_TXT_FILE, DOCKER_API_IMAGE_REQUIREMENTS_TXT_FILE)
    copyfile(REQUIREMENTS_TXT_FILE, DOCKER_WORKER_IMAGE_REQUIREMENTS_TXT_FILE)
    copyfile(REQUIREMENTS_TXT_FILE, DOCKER_SCHEDULER_IMAGE_REQUIREMENTS_TXT_FILE)


def _check_okuna_api_is_running(address, port):
    # Create a TCP socket
    try:
        response = requests.get('http://%s:%s/health/' % (address, port))
        response_status = response.status_code
        return response_status == 200
    except requests.ConnectionError as e:
        return False


def _wait_until_api_is_running(address, port, message='Waiting for server to come up...', sleep=None):
    spinner = Halo(text=message, spinner='dots')
    spinner.start()

    if sleep:
        time.sleep(sleep)

    is_running = _check_okuna_api_is_running(address=address, port=port)

    while not is_running:
        is_running = _check_okuna_api_is_running(address=address, port=port)

    spinner.stop()


def _clean():
    """
    Cleans everything that the okuna-cli has created. Docker volumes, config files, everything.
    :return:
    """
    logger.info('🧹 Cleaning up database')
    subprocess.run(["docker", "volume", "rm", "okuna-api_mariadb"])
    subprocess.run(["docker", "volume", "rm", "okuna-api_redisdb"])

    logger.info('🧹 Cleaning up config files')
    _remove_file_silently(LOCAL_API_ENV_FILE)
    _remove_file_silently(DOCKER_COMPOSE_ENV_FILE)
    _remove_file_silently(OKUNA_CLI_CONFIG_FILE)
    logger.info('✅ Clean up done!')


def _print_okuna_logo():
    print(r"""
   ____  _                      
  / __ \| |                     
 | |  | | | ___   _ _ __   __ _ 
 | |  | | |/ | | | | '_ \ / _` |
 | |__| |   <| |_| | | | | (_| |
  \____/|_|\_\\__,_|_| |_|\__,_|
                                
  """)


def _file_exists(filename):
    return os.path.exists(filename) and os.path.isfile(filename)


def _replace_in_file(filename, texts):
    with open(filename, 'r') as file:
        filedata = file.read()

    # Replace the target string
    for key in texts:
        value = texts[key]
        filedata = filedata.replace(key, value)

    # Write the file out again
    with open(filename, 'w') as file:
        file.write(filedata)


def _ensure_has_local_api_environment_file(okuna_cli_config):
    if _file_exists(LOCAL_API_ENV_FILE):
        return
    logger.info('Local API .env file does not exist. Creating %s' % LOCAL_API_ENV_FILE)

    if not _file_exists(LOCAL_API_ENV_FILE_TEMPLATE):
        raise Exception('Local API .env file template did not exist')

    copyfile(LOCAL_API_ENV_FILE_TEMPLATE, LOCAL_API_ENV_FILE)

    _replace_in_file(LOCAL_API_ENV_FILE, {
        "{{DJANGO_SECRET_KEY}}": okuna_cli_config['djangoSecretKey'],
        "{{SQL_PASSWORD}}": okuna_cli_config['sqlPassword'],
        "{{REDIS_PASSWORD}}": okuna_cli_config['redisPassword'],
    })


def _ensure_has_docker_compose_api_environment_file(okuna_cli_config):
    if _file_exists(DOCKER_COMPOSE_ENV_FILE):
        return
    logger.info('Docker compose env file does not exist. Creating %s' % DOCKER_COMPOSE_ENV_FILE)

    if not _file_exists(DOCKER_COMPOSE_ENV_FILE_TEMPLATE):
        raise Exception('Docker compose env file template did not exist')

    copyfile(DOCKER_COMPOSE_ENV_FILE_TEMPLATE, DOCKER_COMPOSE_ENV_FILE)

    _replace_in_file(DOCKER_COMPOSE_ENV_FILE, {
        "{{DJANGO_SECRET_KEY}}": okuna_cli_config['djangoSecretKey'],
        "{{SQL_PASSWORD}}": okuna_cli_config['sqlPassword'],
        "{{REDIS_PASSWORD}}": okuna_cli_config['redisPassword'],
    })


def _ensure_has_okuna_config_file():
    if _file_exists(OKUNA_CLI_CONFIG_FILE):
        return

    django_secret_key = _get_django_secret_key()
    mysql_password = _get_mysql_password()
    redis_password = _get_redis_password()

    logger.info('Generated DJANGO_SECRET_KEY=%s' % django_secret_key)
    logger.info('Generated SQL_PASSWORD=%s' % mysql_password)
    logger.info('Generated REDIS_PASSWORD=%s' % redis_password)

    logger.info('Config file does not exist. Creating %s' % OKUNA_CLI_CONFIG_FILE)

    if not _file_exists(OKUNA_CLI_CONFIG_FILE_TEMPLATE):
        raise Exception('Config file template did not exists')

    copyfile(OKUNA_CLI_CONFIG_FILE_TEMPLATE, OKUNA_CLI_CONFIG_FILE)

    _replace_in_file(OKUNA_CLI_CONFIG_FILE, {
        "{{DJANGO_SECRET_KEY}}": django_secret_key,
        "{{SQL_PASSWORD}}": mysql_password,
        "{{REDIS_PASSWORD}}": redis_password,
    })


def _bootstrap(is_local_api):
    logger.info('🚀 Bootstrapping Okuna with some data')

    if is_local_api:
        subprocess.run(["./utils/scripts/bootstrap_development_data.sh"])
    else:
        subprocess.run(["docker-compose", "-f", "docker-compose-full.yml", "exec", "webserver",
                        "/bootstrap_development_data.sh"])


def _ensure_has_required_cli_config_files():
    _ensure_has_okuna_config_file()
    with open(OKUNA_CLI_CONFIG_FILE, 'r+') as okuna_cli_config_file:
        okuna_cli_config = json.load(okuna_cli_config_file)
        _ensure_has_docker_compose_api_environment_file(okuna_cli_config=okuna_cli_config)
        _ensure_has_local_api_environment_file(okuna_cli_config=okuna_cli_config)


def _ensure_was_bootstrapped(is_local_api):
    with open(OKUNA_CLI_CONFIG_FILE, 'r+') as okuna_cli_config_file:
        okuna_cli_config = json.load(okuna_cli_config_file)
        if okuna_cli_config['bootstrapped']:
            return

        logger.info('Okuna was not bootstrapped.')

        _bootstrap(is_local_api=is_local_api)

        okuna_cli_config['bootstrapped'] = True
        okuna_cli_config_file.seek(0)
        json.dump(okuna_cli_config, okuna_cli_config_file, indent=4)
        okuna_cli_config_file.truncate()

        logger.info('Okuna was bootstrapped.')


@click.group()
def cli():
    pass


def _down_test():
    """Bring Okuna down"""
    logger.error('⬇️  Bringing the Okuna test services down...')
    subprocess.run(["docker-compose", "-f", "docker-compose-test-services-only.yml", "down"])


def _down_full():
    """Bring Okuna down"""
    logger.error('⬇️  Bringing the whole of Okuna down...')
    subprocess.run(["docker-compose", "-f", "docker-compose-full.yml", "down"])


def _down_services_only():
    """Bring Okuna down"""
    logger.error('⬇️  Bringing the Okuna services down...')
    subprocess.run(["docker-compose", "-f", "docker-compose-services-only.yml", "down"])


@click.command()
def down_services_only():
    _down_services_only()


@click.command()
def down_full():
    _down_full()


@click.command()
def up_full():
    """Bring the whole of Okuna up"""
    _print_okuna_logo()
    _ensure_has_required_cli_config_files()
    _copy_requirements_txt_to_docker_images_dir()

    logger.info('⬆️  Bringing the whole of Okuna up...')

    atexit.register(_down_full)
    subprocess.run(["docker-compose", "-f", "docker-compose-full.yml", "up", "-d", "-V"])

    okuna_api_address = '127.0.0.1'
    okuna_api_port = 80

    _wait_until_api_is_running(address=okuna_api_address, port=okuna_api_port)

    _ensure_was_bootstrapped(is_local_api=False)

    logger.info('🥳  Okuna is live at http://%s:%s.' % (okuna_api_address, okuna_api_port))

    subprocess.run(["docker-compose", "-f", "docker-compose-full.yml", "logs", "--follow", "--tail=0", "webserver"])

    input()


@click.command()
def up_services_only():
    """Bring only the Okuna services up. API is up to you."""
    _print_okuna_logo()
    _ensure_has_required_cli_config_files()
    _copy_requirements_txt_to_docker_images_dir()

    logger.info('⬆️  Bringing only the Okuna services up...')

    atexit.register(_down_services_only)
    subprocess.run(["docker-compose", "-f", "docker-compose-services-only.yml", "up", "-d", "-V"])

    _ensure_was_bootstrapped(is_local_api=True)

    logger.info('🥳  Okuna services are up')

    subprocess.run(["docker-compose", "-f", "docker-compose-services-only.yml", "logs", "--follow"])

    input()


@click.command()
def down_test():
    _down_test()


@click.command()
def up_test():
    """Bring the Okuna test services up"""
    _print_okuna_logo()
    _ensure_has_required_cli_config_files()

    logger.info('⬆️  Bringing the Okuna test services up...')

    atexit.register(_down_test)
    subprocess.run(["docker-compose", "-f", "docker-compose-test-services-only.yml", "up", "-d", "-V"])

    logger.info('🥳  Okuna  tests services are live')

    subprocess.run(
        ["docker-compose", "-f", "docker-compose-test-services-only.yml", "logs", "--follow", "--tail=0"])

    input()


@click.command()
def build_full():
    """Rebuild Okuna services"""
    _ensure_has_required_cli_config_files()
    logger.info('👷‍♀️  Rebuilding Okuna full services...')
    _copy_requirements_txt_to_docker_images_dir()
    subprocess.run(["docker-compose", "-f", "docker-compose-full.yml", "build"])


@click.command()
def build_services_only():
    """Rebuild Okuna services"""
    _ensure_has_required_cli_config_files()
    logger.info('👷‍♀️  Rebuilding only Okuna services...')
    _copy_requirements_txt_to_docker_images_dir()
    subprocess.run(["docker-compose", "-f", "docker-compose-services-only.yml", "build"])


@click.command()
def status():
    """Get Okuna status"""
    logger.info('🕵️‍♂️  Retrieving services status...')
    subprocess.run(["docker-compose", "ps"])


@click.command()
def clean():
    """Bootstrap Okuna"""
    _clean()


cli.add_command(up_full)
cli.add_command(down_full)
cli.add_command(up_test)
cli.add_command(down_test)
cli.add_command(up_services_only)
cli.add_command(down_services_only)
cli.add_command(build_full)
cli.add_command(build_services_only)
cli.add_command(clean)
cli.add_command(status)

if __name__ == '__main__':
    cli()
