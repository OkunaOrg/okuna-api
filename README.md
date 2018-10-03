<img alt="Open book logo" src="https://snag.gy/yWbLr1.jpg" width="200">

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

Clone the repository

```sh
git clone git@github.com:OpenbookOrg/openbook-api.git
```

Create and configure your .env file

```bash
cp sample.env .env
nano .env
```

Install the dependencies
```bash
pipenv install
```

Activate the pipenv environment
```bash
pipenv shell
```

Serve with hot reload at http://127.0.0.1:8000
```bash
python manage.py runserver
```

<br>

## FAQ

### Double logging in console

The local development server runs a separate process for the auto-reloader. You can turn off the auto-reload process by passing the --noreload flag.

````bash
python manage.py runserver --noreload
````

#### Happy coding 🎉!

