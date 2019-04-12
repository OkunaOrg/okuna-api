<img alt="Open book logo" src="https://snag.gy/oaVCPq.jpg" width="200">

[![CircleCI](https://circleci.com/gh/OpenbookOrg/openbook-api.svg?style=svg&circle-token=b41cbfe3c292a3e900120dac5713328b1e754d20)](https://circleci.com/gh/OpenbookOrg/openbook-api) [![Maintainability](https://api.codeclimate.com/v1/badges/5e6ae40e9d945cad0591/maintainability)](https://codeclimate.com/repos/5bbf4878e46c0d3b620000a2/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/5e6ae40e9d945cad0591/test_coverage)](https://codeclimate.com/repos/5bbf4878e46c0d3b620000a2/test_coverage) [![gitmoji badge](https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=flat-square)](https://github.com/carloscuesta/gitmoji)


The API server for Openbook.

## Table of contents

- [Requirements](#requirements)
- [Project overview](#project-overview)
- [Contributing](#contributing)
    + [Code of Conduct](#code-of-conduct)
    + [License](#license)
    + [Other issues](#other-issues)
    + [Git commit message conventions](#git-commit-message-conventions)
- [Getting started](#getting-started)
- [FAQ](#faq)
    + [Double logging in console](#double-logging-in-console)

## Requirements

* [Pipenv](https://github.com/pypa/pipenv)
* [MySQL](https://www.mysql.com/de/products/community/)
* [Redis](https://redis.io/)
* [libmagic](https://www.darwinsys.com/file/)

## Project overview

The project is a [Django](https://www.djangoproject.com/start/) application. 

## Contributing

There are many different ways to contribute to the website development, just find the one that best fits with your skills and open an issue/pull request in the repository.

Examples of contributions we love include:

- **Code patches**
- **Bug reports**
- **Patch reviews**
- **Translations**
- **UI enhancements**

#### Code of Conduct

Please read and follow our [Code of Conduct](https://github.com/OpenBookOrg/openbook-api/blob/master/CODE_OF_CONDUCT.md).

#### License

Every contribution accepted is licensed under [AGPL v3.0](http://www.gnu.org/licenses/agpl-3.0.html) or any later version. 
You must be careful to not include any code that can not be licensed under this license.

Please read carefully [our license](https://github.com/OpenBookOrg/openbook-org-backend/blob/master/LICENSE.txt) and ask us if you have any questions.

#### Responsible disclosure

Cyber-hero? Check out our [Vulnerability Disclosure page](https://www.open-book.org/en/vulnerability-report).

#### Other issues

We're available almost 24/7 in the Openbook slack channel. [Join us!](https://join.slack.com/t/openbookorg/shared_invite/enQtNDI2NjI3MDM0MzA2LTYwM2E1Y2NhYWRmNTMzZjFhYWZlYmM2YTQ0MWEwYjYyMzcxMGI0MTFhNTIwYjU2ZDI1YjllYzlhOWZjZDc4ZWY)

#### Git commit message conventions

Help us keep the repository history consistent 🙏!

We use [gitmoji](https://gitmoji.carloscuesta.me/) as our git message convention.

If you're using git in your command line, you can download the handy tool [gitmoji-cli](https://github.com/carloscuesta/gitmoji-cli).

## Getting started

#### Clone the repository

```bash
git clone git@github.com:OpenbookOrg/openbook-api.git
```

#### Create and configure your .env file

```bash
cp .env.sample .env
nano .env
```

#### Install the dependencies
```bash
pipenv install
```

#### Activate the pipenv environment
```bash
pipenv shell
```

#### Run the database migrations
```bash
python manage.py migrate
```

#### Collect the media fixtures

```bash
python manage.py collectmedia
```

#### Load the fixtures
```bash
python manage.py loaddata circles.json emoji-groups.json emojis.json badges.json categories.json
```

#### Serve with hot reload
For local API development it suffices to bind the server to localhost:
```bash
python manage.py runserver
```

For app development you have to bind the server to your local network:
```bash
python manage.py runserver 0.0.0.0:8000
```

<br>

## Django Custom Commands

### `manage.py create_invite`

Creates a user invite and outputs its token.
Required for creating a new account.

```bash
usage: manage.py create_invite [-h] [--email EMAIL] [--username USERNAME] [--name NAME] [--badge BADGE]
```

## Troubleshooting

### macOS

#### The `pipenv install` command fails

You probably installed openssl via [Homebew](https://brew.sh/index_de), make sure to follow the instructions that are given when you type `brew info openssl`.

## FAQ

### Double logging in console

The local development server runs a separate process for the auto-reloader. You can turn off the auto-reload process by passing the --noreload flag.

````bash
python manage.py runserver --noreload
````

#### Happy coding 🎉!

