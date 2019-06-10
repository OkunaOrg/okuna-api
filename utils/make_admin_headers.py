import os
import argparse
from jinja2 import Environment, FileSystemLoader


def make_eb_config_block_admin(lb_name, utils_dir):

    j2_env = Environment(loader=FileSystemLoader(utils_dir), autoescape=True)
    return j2_env.get_template(
            'templates/eb_extensions/block_admin.config.yml'
           ).render(
             LB_NAME=lb_name
        )


def make_eb_config_admin(sauth_server_name, utils_dir):

    j2_env = Environment(loader=FileSystemLoader(utils_dir), autoescape=True)
    return j2_env.get_template(
            'templates/eb_extensions/admin.config.yml'
           ).render(
             SAUTH_SERVER_NAME=sauth_server_name
    )


def write_eb_config(dest, contents):

    with open(dest, 'w') as fd:
        fd.write(contents)


def main():

    parser = argparse.ArgumentParser(
                    description='EB Extension Admin Conf Maker'
                    )

    parser.add_argument('--lb-name', type=str,
                        required=True,
                        help='The value of the loadbalancer.')

    parser.add_argument('--sauth-server-name', type=str,
                        required=True,
                        help='The value of the sauth server.')

    args = parser.parse_args()

    UTILS_DIR = os.path.dirname(os.path.abspath(__file__))

    admin = make_eb_config_admin(args.sauth_server_name, UTILS_DIR)
    block_admin = make_eb_config_block_admin(args.lb_name, UTILS_DIR)

    admin_dest = './.ebextensions/admin.config'
    block_admin_dest = './.ebextensions/block_admin.config'

    write_eb_config(admin_dest, admin)
    write_eb_config(block_admin_dest, block_admin)


if __name__ == '__main__':
    main()
