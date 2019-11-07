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

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(name)s -> %(message)s'))

logger = colorlog.getLogger('🤖')
logger.addHandler(handler)

logger.setLevel(level=logging.DEBUG)

current_dir = os.path.dirname(__file__)

OKUNA_CLI_CONFIG_FILE = os.path.join(current_dir, '.okuna-cli.json')
OKUNA_CLI_CONFIG_FILE_TEMPLATE = os.path.join(current_dir, 'templates/.okuna-cli.json')

OKUNA_API_ADDRESS = '127.0.0.1'
OKUNA_API_PORT = 80

CONTEXT_SETTINGS = dict(
    default_map={}
)


def _check_okuna_api_is_running():
    # Create a TCP socket
    try:
        response = requests.get('http://%s:%s/health/' % (OKUNA_API_ADDRESS, OKUNA_API_PORT))
        response_status = response.status_code
        return response_status == 200
    except requests.ConnectionError as e:
        return False


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
    subprocess.run(["docker-compose", "down"])


@click.command()
def up():
    """Bring Okuna up"""
    _print_okuna_logo()
    logger.info('⬆️  Bringing Okuna up...')

    atexit.register(_down)
    subprocess.run(["docker-compose", "up", "-d"])
    spinner = Halo(text='Waiting for server to come up...', spinner='dots')
    spinner.start()

    is_running = _check_okuna_api_is_running()

    while not is_running:
        is_running = _check_okuna_api_is_running()

    spinner.stop()

    logger.info('✅️  Okuna is live at http://%s:%s' % (OKUNA_API_ADDRESS, OKUNA_API_PORT))
    input("⌨️  Press enter to exit")
    # logger.info('Okuna docker service started successfully')
    # subprocess.run(["docker", 'exec', '-it', 'okuna-api', '/bin/bash', '-c', 'echo hello'])


@click.command()
def status():
    """Bring Okuna down"""
    logger.info('🕵️‍♂️  Retrieving services status...')
    subprocess.run(["docker-compose", "ps"])


@click.command()
def bootstrap():
    """Bootstrap Okuna"""
    logger.info('BOOTSTRAP')


cli.add_command(up)
cli.add_command(bootstrap)
cli.add_command(status)

if __name__ == '__main__':
    cli()
