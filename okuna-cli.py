import click
import subprocess
import colorlog
import logging
import os.path
from shutil import copyfile
import json

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(name)s -> %(message)s'))

logger = colorlog.getLogger('🤖 Okuna CLI')
logger.addHandler(handler)

logger.setLevel(level=logging.DEBUG)

current_dir = os.path.dirname(__file__)

OKUNA_CLI_CONFIG_FILE = os.path.join(current_dir, '.okuna-cli.json')
OKUNA_CLI_CONFIG_FILE_TEMPLATE = os.path.join(current_dir, 'templates/.okuna-cli.json')

CONTEXT_SETTINGS = dict(
    default_map={}
)


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


@click.command()
def up():
    """Bring Okuna up"""
    _ensure_was_bootstrapped()
    logger.info('Bringing services up...')
    subprocess.run(["docker-compose", "up", "-d"])
    logger.info('Okuna docker service started successfully')


@click.command()
def down():
    """Bring Okuna down"""
    logger.info('Bringing services down...')
    subprocess.run(["docker-compose", "down"])


@click.command()
def status():
    """Bring Okuna down"""
    logger.info('Checking services status...')
    subprocess.run(["docker-compose", "ps"])


@click.command()
def bootstrap():
    """Bootstrap Okuna"""
    logger.info('BOOTSTRAP')


cli.add_command(up)
cli.add_command(down)
cli.add_command(bootstrap)
cli.add_command(status)

if __name__ == '__main__':
    cli()
