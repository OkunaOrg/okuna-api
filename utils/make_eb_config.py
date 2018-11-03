import os
import argparse
from jinja2 import Environment, FileSystemLoader


def make_eb_config(application_name, default_region):
    # Capture our current directory
    UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
    # Create the jinja2 environment.
    # Notice the use of trim_blocks, which greatly helps control whitespace.
    j2_env = Environment(loader=FileSystemLoader(UTILS_DIR))
    return j2_env.get_template('templates/eb/config.yml').render(
        APPLICATION_NAME=application_name,
        DEFAULT_REGION=default_region
    )


def write_eb_config(dest, application_name, default_region):
    contents = make_eb_config(application_name, default_region)
    fh = open(dest, 'w')
    fh.write(contents)
    fh.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EB Config Maker')
    # Optional argument
    parser.add_argument('--dest', type=str,
                        help='The destination of the generated eb config',
                        default='./.elasticbeanstalk/config.yml')

    parser.add_argument('--name', type=str,
                        required=True,
                        help='The name of the application')

    parser.add_argument('--region', type=str,
                        required=True,
                        help='The default application region')

    args = parser.parse_args()

    write_eb_config(args.dest, application_name=args.name, default_region=args.region)
