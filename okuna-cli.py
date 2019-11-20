import time

import click
import subprocess
import colorlog
import logging
import os.path
from shutil import copyfile
import json
import atexit
import os
import requests
from halo import Halo
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(name)s -> %(message)s'))

logger = colorlog.getLogger('🤖')
logger.addHandler(handler)

logger.setLevel(level=logging.DEBUG)

current_dir = os.path.dirname(__file__)

OKUNA_CLI_CONFIG_FILE = os.path.join(current_dir, '.okuna-cli.json')
OKUNA_CLI_CONFIG_FILE_TEMPLATE = os.path.join(current_dir, 'templates/.okuna-cli.json')

REQUIREMENTS_TXT_FILE = os.path.join(current_dir, 'requirements.txt')
DOCKER_API_IMAGE_REQUIREMENTS_TXT_FILE = os.path.join(current_dir, '.docker', 'api', 'requirements.txt')
DOCKER_WORKER_IMAGE_REQUIREMENTS_TXT_FILE = os.path.join(current_dir, '.docker', 'worker', 'requirements.txt')
DOCKER_SCHEDULER_IMAGE_REQUIREMENTS_TXT_FILE = os.path.join(current_dir, '.docker', 'scheduler', 'requirements.txt')
DOCKER_API_TEST_IMAGE_REQUIREMENTS_TXT_FILE = os.path.join(current_dir, '.docker', 'api-test', 'requirements.txt')

OKUNA_API_ADDRESS = '127.0.0.1'
OKUNA_API_PORT = 80

CONTEXT_SETTINGS = dict(
    default_map={}
)


def _copy_requirements_txt_to_docker_images_dir():
    copyfile(REQUIREMENTS_TXT_FILE, DOCKER_API_IMAGE_REQUIREMENTS_TXT_FILE)
    copyfile(REQUIREMENTS_TXT_FILE, DOCKER_WORKER_IMAGE_REQUIREMENTS_TXT_FILE)
    copyfile(REQUIREMENTS_TXT_FILE, DOCKER_SCHEDULER_IMAGE_REQUIREMENTS_TXT_FILE)
    copyfile(REQUIREMENTS_TXT_FILE, DOCKER_API_TEST_IMAGE_REQUIREMENTS_TXT_FILE)


def _check_okuna_api_is_running():
    # Create a TCP socket
    try:
        response = requests.get('http://%s:%s/health/' % (OKUNA_API_ADDRESS, OKUNA_API_PORT))
        response_status = response.status_code
        return response_status == 200
    except requests.ConnectionError as e:
        return False


def _wait_until_api_is_running(message='Waiting for server to come up...', sleep=None):
    spinner = Halo(text=message, spinner='dots')
    spinner.start()

    if sleep:
        time.sleep(sleep)

    is_running = _check_okuna_api_is_running()

    while not is_running:
        is_running = _check_okuna_api_is_running()

    spinner.stop()


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


def _ensure_has_okuna_config_file():
    if _file_exists(OKUNA_CLI_CONFIG_FILE):
        return
    logger.info('Config file does not exist. Creating %s' % OKUNA_CLI_CONFIG_FILE)

    if not _file_exists(OKUNA_CLI_CONFIG_FILE_TEMPLATE):
        raise Exception('Config file template did not exists')

    copyfile(OKUNA_CLI_CONFIG_FILE_TEMPLATE, OKUNA_CLI_CONFIG_FILE)


def _bootstrap():
    logger.info('Okuna was not bootstrapped. Will bootstrap...')
    exit(0)


def _ensure_was_bootstrapped():
    _ensure_has_okuna_config_file()
    with open(OKUNA_CLI_CONFIG_FILE, 'r+') as okuna_cli_config_file:
        okuna_cli_config = json.load(okuna_cli_config_file)
        if okuna_cli_config['bootstrapped']:
            return
        _bootstrap()


@click.group()
def cli():
    pass


def _down():
    """Bring Okuna down"""
    logger.error('⬇️  Bringing Okuna down...')
    subprocess.run(["docker-compose", "-f", "docker-compose.yml", "down"])


class UpCommandFileChangedEventHandler(FileSystemEventHandler):
    file_cache = {}
    handling_change = False

    def on_moved(self, event):
        super(UpCommandFileChangedEventHandler, self).on_moved(event)
        self._handle_change(event)

    def on_created(self, event):
        super(UpCommandFileChangedEventHandler, self).on_created(event)
        self._handle_change(event)

    def on_deleted(self, event):
        super(UpCommandFileChangedEventHandler, self).on_deleted(event)
        self._handle_change(event)

    def on_modified(self, event):
        super(UpCommandFileChangedEventHandler, self).on_modified(event)
        self._handle_change(event)

    def _handle_change(self, event):
        seconds = int(time.time())
        key = (seconds, event.src_path)
        if key in self.file_cache or self.handling_change:
            return
        self.file_cache[key] = True
        self.handling_change = True

        if event.src_path.endswith('.py'):
            # Let the manage.py watcher pick up the change with a 1 sec sleep
            _wait_until_api_is_running(sleep=1, message='Detected file changes, waiting for server to come up...')
        self.handling_change = False


@click.command()
def up():
    """Bring Okuna up"""
    _print_okuna_logo()
    _copy_requirements_txt_to_docker_images_dir()
    logger.info('⬆️  Bringing Okuna up...')

    atexit.register(_down)
    subprocess.run(["docker-compose", "-f", "docker-compose.yml", "up", "-d"])

    _wait_until_api_is_running()

    logger.info('🥳  Okuna is live at http://%s:%s' % (OKUNA_API_ADDRESS, OKUNA_API_PORT))

    subprocess.run(["docker-compose", "-f", "docker-compose.yml", "logs", "--follow", "--tail=0",  "webserver"])

    input()


@click.command()
def build():
    """Rebuild Okuna services"""
    logger.info('👷‍♀️  Rebuilding Okuna services...')
    subprocess.run(["docker-compose", "build"])


@click.command()
def status():
    """Get Okuna status"""
    logger.info('🕵️‍♂️  Retrieving services status...')
    subprocess.run(["docker-compose", "ps"])


@click.command()
def bootstrap():
    """Bootstrap Okuna"""
    logger.info('BOOTSTRAP')


cli.add_command(up)
cli.add_command(build)
cli.add_command(bootstrap)
cli.add_command(status)

if __name__ == '__main__':
    cli()
