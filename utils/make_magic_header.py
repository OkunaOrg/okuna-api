import os
import argparse
from jinja2 import Environment, FileSystemLoader


def make_eb_config(header_name, header_value):
    # Capture our current directory
    UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    j2_env = Environment(loader=FileSystemLoader(UTILS_DIR), autoescape=True)
    return j2_env.get_template('templates/eb_extensions/magic_header.config.yml').render(
        HEADER_NAME=header_name,
        HEADER_VALUE=header_value
    )


def write_eb_config(dest, header_name, header_value):
    contents = make_eb_config(header_name, header_value)
    fh = open(dest, 'w')
    fh.write(contents)
    fh.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EB Extension Magic Header Maker')
    # Optional argument
    parser.add_argument('--dest', type=str,
                        help='The destination of the generated ebextension config',
                        default='./.ebextensions/magic_header.config')

    parser.add_argument('--name', type=str,
                        required=True,
                        help='The name of the magic header')

    parser.add_argument('--value', type=str,
                        required=True,
                        help='The secret value of the magic header')

    args = parser.parse_args()

    write_eb_config(args.dest, header_name=args.name, header_value=args.value)
