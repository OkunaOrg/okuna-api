import os
import argparse
from jinja2 import Environment, FileSystemLoader


def make_eb_basic_auth_config(htpasswd_contents):
    # Capture our current directory
    UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    j2_env = Environment(loader=FileSystemLoader(UTILS_DIR))
    return j2_env.get_template('templates/eb/basic_auth.config.yml').render(
        HTPASSWD=htpasswd_contents
    )


def write_eb_config(dest, htpasswd_contents):
    contents = make_eb_basic_auth_config(htpasswd_contents)
    fh = open(dest, 'w')
    fh.write(contents)
    fh.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EB Config Maker')
    # Optional argument
    parser.add_argument('--dest', type=str,
                        help='The destination of the generated eb config',
                        default='./.ebextensions/basic_auth.config')

    parser.add_argument('--htpasswd', type=str,
                        required=True,
                        help='The htpasswd file contents')

    args = parser.parse_args()

    write_eb_config(args.dest, htpasswd_contents=args.htpasswd)
