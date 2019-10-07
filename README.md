<img alt="Okuna logo" src="https://i.snag.gy/FAgp8K.jpg" width="200">

[![CircleCI](https://circleci.com/gh/OkunaOrg/okuna-api.svg?style=svg&circle-token=b41cbfe3c292a3e900120dac5713328b1e754d20)](https://circleci.com/gh/OkunaOrg/okuna-api) [![Maintainability](https://api.codeclimate.com/v1/badges/5e6ae40e9d945cad0591/maintainability)](https://codeclimate.com/repos/5bbf4878e46c0d3b620000a2/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/5e6ae40e9d945cad0591/test_coverage)](https://codeclimate.com/repos/5bbf4878e46c0d3b620000a2/test_coverage) [![gitmoji badge](https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=flat-square)](https://github.com/carloscuesta/gitmoji)


The API server for Okuna.

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
* [ffmpeg](https://ffmpeg.org/)

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

Please read and follow our [Code of Conduct](https://github.com/OkunaOrg/okuna-api/blob/master/CODE_OF_CONDUCT.md).

#### License

Every contribution accepted is licensed under [AGPL v3.0](http://www.gnu.org/licenses/agpl-3.0.html) or any later version. 
You must be careful to not include any code that can not be licensed under this license.

Please read carefully [our license](https://github.com/OkunaOrg/okuna-api/blob/master/LICENSE.txt) and ask us if you have any questions.

#### Responsible disclosure

Cyber-hero? Check out our [Vulnerability Disclosure page](https://www.open-book.org/en/vulnerability-report).

#### Other issues

We're available almost 24/7 in the Okuna slack channel. [Join us!](https://join.slack.com/t/okunaorg/shared_invite/enQtNDI2NjI3MDM0MzA2LTYwM2E1Y2NhYWRmNTMzZjFhYWZlYmM2YTQ0MWEwYjYyMzcxMGI0MTFhNTIwYjU2ZDI1YjllYzlhOWZjZDc4ZWY)

#### Git commit message conventions

Help us keep the repository history consistent 🙏!

We use [gitmoji](https://gitmoji.carloscuesta.me/) as our git message convention.

If you're using git in your command line, you can download the handy tool [gitmoji-cli](https://github.com/carloscuesta/gitmoji-cli).

## Getting started

#### Clone the repository

```bash
git clone git@github.com:OkunaOrg/okuna-api.git
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
python manage.py loaddata circles.json emoji-groups.json emojis.json badges.json categories.json languages.json
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

#### Spawn an rq-worker

We use rq-workers to process media, deliver push notifications and more.

```bash
python manage.py rqworker
```

#### Spawn an rq-scheduler

We use rq-schedulers to run one time or repetitive tasks like cleaning up failed to upload posts.

```bash
python manage.py rqscheduler
```

To schedule a job, go to the `/admin/scheduler` route.

The available jobs are

##### openbook_posts.jobs.flush_draft_posts

Cleans up all draft posts which have not being modified for a day.

Should be run every hour or so.

##### openbook_posts.jobs.curate_top_posts

Curates the top posts, which end up in the explore tab.

Should be run every 5 minutes or so.


##### openbook_posts.jobs.clean_top_posts

Cleans the top posts which should no longer be top posts.

This happens if an item is soft deleted, reported and approved

Should be run every 5 minutes or so.






<br>

## Django Translations

1. Use `./manage.py makemessages -l es` to generate messages. Doesn't matter which language we target, the translation tool is agnostic.
2. This generates a new `django.po` file in the `locale/es/LC_MESSAGES/` folder. It will have all the
source strings and a place to enter the translation strings. It doesnt overwrite previous translations.
3. Sometimes, if django is confused, it marks a string as fuzzy. So do search for  the word 'fuzzy' in `django.po`
4. If you find a fuzzy string, you can resolve it manually. Finally each string should like this
```
#: openbook_lists/validators.py:10   <- place where the string occurs in code
msgid "The list does not exist."     <- english translations  
msgstr "Die Liste ist nicht vorhanden."   <-- this will be empty for new strings
```
5. Upload this `django.po` file to https://crowdin.com/project/okuna/settings#files by pressing `Update` next to the existing `django.po` file.
6. Once all language volunteers have translated the new strings, download all the `django.po` files for each locale and 
put them in their respective folders.
7. Run `./manage.py compilemessages` to auto-generate `django.mo` files. 
8. You need to checkin both `django.po` and `django.mo` files for each locale.


## Django Custom Commands

### `manage.py create_invite`

Creates a user invite and outputs its token.
Required for creating a new account.

```bash
usage: manage.py create_invite [-h] [--email EMAIL] [--username USERNAME] [--name NAME] [--badge BADGE]
```

### `manage.py import_invites`

Imports user invites from a kickstarter/indiegogo csv

```bash
usage: manage.py import_invites [-h] [--indiegogo PATH_TO_CSV] [--kickstarter PATH_TO_CSV]
```


### `manage.py send_invites`

Send invite emails to all user invites who have not been sent the email. 

```bash
usage: manage.py send_invites [-h]
```

### `manage.py allocate_invites`

Assign user invites to all or specific users. 

```bash
usage: manage.py allocate_invites [-h] [--count INCREMENT_INVITES_BY_COUNT] [--total TOTAL_INVITE_COUNT_TO_SET] [--username USERNAME]
```

### `manage.py create_post_media_thumbnails`

Creates media_thumbnail, media_height and media_width for items which don't have it using the Post -> PostMedia relationship.

The command was created as a one off migration tool.

```bash
usage: manage.py create_post_media_thumbnails
```

### `manage.py migrate_post_images`

Migrates Post -> PostImage to Post -> PostMedia -> PostImage.

The command was created as a one off migration tool.

### `manage.py import_proxy_blacklisted_domains`

Import a list of domains to be blacklisted when calling the `ProxyAuth` and `ProxyDomainCheck` APIs.

```bash
usage: manage.py import_proxy_blacklisted_domains [--file The path to the file with the domains to import]
```

#### Example

```bash
python manage.py import_proxy_blacklisted_domains --file ./openbook_common/misc/domain_blacklists/porn/domains
```

### `manage.py flush_proxy_blacklisted_domains`

Flush all of the blacklisted proxy domains

```bash
usage: manage.py flush_proxy_blacklisted_domains
```

### Crowdin translations update
Download the latest django.po files in the respective locale/ folders from crowdin. 
Then locally run all or some of these commands depending on which models need updating.
It will update the `.json` files, then check them in.
```$xslt
./manage.py shell < openbook_common/i18n/update_translations_emoji_groups.py
./manage.py shell < openbook_common/i18n/update_translations_emojis.py
./manage.py shell < openbook_moderation/i18n/update_translations.py
./manage.py shell < openbook_categories/i18n/update_translations.py
```

## Docker Compose

### Replace .env settings
```bash
# Relational Database Service configuration
RDS_DB_NAME=okuna
RDS_USERNAME=root
RDS_PASSWORD=okuna
RDS_HOSTNAME=db.okuna
RDS_PORT=3306
RDS_HOSTNAME_READER=db.okuna
RDS_HOSTNAME_WRITER=db.okuna
```

### Build the container
```bash
usage: docker-compose build
```

### Run the container
```bash
usage: docker-compose up (-d in background)
```

### Visit the static webserver IP
http://172.16.16.1:80

### Overrides
Copy `docker-compose.override.yml.dist` to `docker-compose.override.yml` to override any settings. By default it will override the network information and fallback to localhost:80/443/3306. [Docker-Compose YML Reference](https://docs.docker.com/compose/compose-file)

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

