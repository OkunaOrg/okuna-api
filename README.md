<img alt="Okuna logo" src="https://i.snag.gy/FAgp8K.jpg" width="200">

[![CircleCI](https://circleci.com/gh/OkunaOrg/okuna-api.svg?style=svg&circle-token=b41cbfe3c292a3e900120dac5713328b1e754d20)](https://circleci.com/gh/OkunaOrg/okuna-api) [![Maintainability](https://api.codeclimate.com/v1/badges/5e6ae40e9d945cad0591/maintainability)](https://codeclimate.com/repos/5bbf4878e46c0d3b620000a2/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/5e6ae40e9d945cad0591/test_coverage)](https://codeclimate.com/repos/5bbf4878e46c0d3b620000a2/test_coverage) [![gitmoji badge](https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67.svg?style=flat-square)](https://github.com/carloscuesta/gitmoji)


The API server for Okuna.

## Table of contents

- [Requirements](#requirements)
- [Project overview](#project-overview)
- [Contributing](#contributing)
    + [Code of Conduct](#code-of-conduct)
    + [License](#license)
    + [Responsible disclosure](#responsible-disclosure)
    + [Other issues](#other-issues)
    + [Git commit message conventions](#git-commit-message-conventions)
- [Getting started](#getting-started)
  * [Clone the repository](#clone-the-repository)
  * [Meet the Okuna CLI](#meet-the-okuna-cli)
  * [Okuna CLI Operational Modes](#okuna-cli-operational-modes)
  * [Full mode](#full-mode)
    + [Installation](#installation)
    + [Available commands](#available-commands)
      - [up-full](#up-full)
      - [down-full](#down-full)
  * [Services-only mode](#services-only-mode)
    + [Installation](#installation-1)
    + [Available commands](#available-commands-1)
      - [up-services-only](#up-services-only)
      - [down-services-only](#down-services-only)
    + [Running the Okuna API server locally](#running-the-okuna-api-server-locally)
  * [Available test data](#available-test-data)
  * [Other Okuna CLI commands](#other-okuna-cli-commands)
    + [clean](#clean)
  * [Okuna CLI behind the scenes](#okuna-cli-behind-the-scenes)
    + [docker-compose](#docker-compose)
    + [Environment files](#environment-files)
- [Available Django commands](#available-django-commands)
  * [Official Django commands](#official-django-commands)
    + [`manage.py migrate`](#managepy-migrate)
    + [`manage.py collectmedia`](#managepy-collectmedia)
    + [`manage.py loaddata`](#managepy-loaddata)
  * [Custom django commands](#custom-django-commands)
    + [`manage.py create_invite`](#managepy-create-invite)
    + [`manage.py import_invites`](#managepy-import-invites)
    + [`manage.py reset_invite_email_boolean`](#managepy-reset-invite-email-boolean)
    + [`manage.py send_invites`](#managepy-send-invites)
    + [`manage.py create_post_media_thumbnails`](#managepy-create-post-media-thumbnails)
    + [`manage.py migrate_post_images`](#managepy-migrate-post-images)
    + [`manage.py import_proxy_blacklisted_domains`](#managepy-import-proxy-blacklisted-domains)
      - [Example](#example)
    + [`manage.py flush_proxy_blacklisted_domains`](#managepy-flush-proxy-blacklisted-domains)
    + [manage.py worker_health_check](#managepy-worker-health-check)
    + [Crowdin translations update](#crowdin-translations-update)
- [Available Django jobs](#available-django-jobs)
  * [openbook_posts.jobs.flush_draft_posts](#openbook-postsjobsflush-draft-posts)
  * [openbook_posts.jobs.curate_top_posts](#openbook-postsjobscurate-top-posts)
  * [openbook_posts.jobs.clean_top_posts](#openbook-postsjobsclean-top-posts)
- [Translations](#translations)
- [FAQ](#faq)
  * [Double logging in console](#double-logging-in-console)


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

Cyber-hero? Check out our [Vulnerability Disclosure page](https://www.okuna.io/en/vulnerability-report).

#### Other issues

We're available almost 24/7 in the Okuna slack channel. [Join us!](https://join.slack.com/t/okunaorg/shared_invite/enQtNDI2NjI3MDM0MzA2LTYwM2E1Y2NhYWRmNTMzZjFhYWZlYmM2YTQ0MWEwYjYyMzcxMGI0MTFhNTIwYjU2ZDI1YjllYzlhOWZjZDc4ZWY)

#### Git commit message conventions

Help us keep the repository history consistent 🙏!

We use [gitmoji](https://gitmoji.carloscuesta.me/) as our git message convention.

If you're using git in your command line, you can download the handy tool [gitmoji-cli](https://github.com/carloscuesta/gitmoji-cli).

## Getting started

### Clone the repository

Run the following in your command line

```bash
git clone git@github.com:OkunaOrg/okuna-api.git && cd okuna-api
```

### Meet the Okuna CLI

The Okuna CLI is built to run a development instance of Okuna loaded with some test data, with a single command.

### Okuna CLI Operational Modes

You can use the CLI in two modes.

1. [Full mode](#full-mode) - **Best for Okuna mobile/web app development**
2. [Services-only mode](#services-only-mode) - **Best for Okuna API development**

Depending on the kind of development you would like to do, follow the instructions below for your chosen mode. 

### Full mode

**Best for Mobile/web app development**

This mode brings a whole Okuna instance up, ready to use with a local Okuna mobile/web app. 

#### Installation

Make sure the following are installed

* [Python 3.5+](https://realpython.com/installing-python/)
* [docker-compose](https://docs.docker.com/compose/install/)

Install the Okuna CLI python packages

```bash
pip install -r requirements-cli-only.txt
```

#### Available commands

##### up-full

**Starts Okuna**

Run the following in your terminal

```bash
python okuna-cli.py up-full
```

🥳 Congrats, you should now have both the whole of Okuna running on port **80**.

##### down-full

**Shuts Okuna down**

When existing the command that starts Okuna by pressing CTRL + C / CMD + C, Okuna will also be stopped.

If the process was abruptly terminated and Okuna is still running in the background you can also run

```bash
python okuna-cli.py down-full
``` 

### Services-only mode

**Best for API development**

The Okuna services are a SQL server, a Redis server, a job scheduler server and a job worker server.

This mode brings these services up but **not** the Okuna API itself, 
you are to run the API locally instead for a better development experience.

#### Installation

Make sure the following are installed

* [Python 3.5+](https://realpython.com/installing-python/)
* [docker-compose](https://docs.docker.com/compose/install/)

Install the Okuna python packages

```bash
pip install -r requirements.txt
```

Make the `bootstrap_development_data.sh` executable

```bash
chmod ./utils/scripts/bootstrap_development_data.sh +x
```

#### Available commands

##### up-services-only

**Starts the Okuna services**

Run the following in your terminal

```bash
python okuna-cli.py up-services-only
```

##### down-services-only

**Stops the Okuna services**

When existing the command that starts Okuna by pressing CTRL + C / CMD + C, Okuna will also be stopped.

If the process was abruptly terminated and Okuna is still running in the background you can also run

```bash
python okuna-cli.py down-services-only
``` 

#### Running the Okuna API server locally

Once the Okuna services are up (using the up-services-only command), start the Okuna API locally by running

```bash
python manage.py runserver
```

This will start the API server on localhost:8000.

If you would like to expose the server on your network, for example, for testing the API server
on your mobile device connected to the same network, run the following instead.

```bash
python manage.py runserver 0.0.0.0:8000
```

🥳 Congrats, you should now have both the Okuna services and the Okuna API running in sync.

### Available test data

Within the provisioned Okuna development instance, you will find some test accounts and respective posts/communities.

The credentials for these accounts are the following.


````bash
username:martha
password:changeme123!
````

````bash
username:mike
password:changeme123!
````

````bash
username:miguel
password:changeme123!
````

### Other Okuna CLI commands

#### clean

** Cleans everything related to the Okuna CLI**

This will dispose of the employed database and generated config files.

Use this if you want to get a fresh version of Okuna next time you use the Okuna CLI `up` commands.

```bash
python okuna-cli.py clean
``` 
 
### Okuna CLI behind the scenes

This section will try to demistify what the Okuna CLI does.

#### docker-compose

Behind the scenes, the Okuna CLI uses [docker-compose](https://docs.docker.com/compose/) to spawn
and coordinate the following docker services.

* **webserver** - A server running the Okuna API
* **db** - A server with a MariaDB database
* **redis** - A server with a Redis database
* **scheduler** - A server responsible for running the scheduled Okuna jobs such as curating Explore/Top posts.
* **worker** - A server responsible for processing the Okuna jobs such as publishing a post or curating posts.

On services-only mode, the webserver is not spawned.

#### Environment files

When starting okuna-cli for the first time, 3 files will be generated

* **.okuna-cli.json** - Contains a flag indicating whether the Okuna instance was bootstrapped and the secret keys employed
    to kickstart all other services
* **.env** - The environment file used when running the Okuna CLI in services-only mode.
* **.docker-compose.env** - The environment file used in all Okuna docker compose services


## Available Django commands

A list of official and custom django commands that might come handy.

If running the API locally you can execute them as 

```bash
python manage.py $command
```

If running the API with the Okuna CLI full mode, you can execute them by connecting to the webserver
machine by running

```bash
docker-compose -f docker-compose-full.yml exec webserver "/bin/bash"
```

Inside the machine you can then execute the commands as 

```bash
python manage.py $command
```

### Official Django commands

#### `manage.py migrate`

Run the database migrations

```bash
python manage.py migrate
```

#### `manage.py collectmedia`

Collect the media fixtures

```bash
python manage.py collectmedia
```

#### `manage.py loaddata`

Load the given data fixture file into the database

```bash
python manage.py loaddata circles.json emoji-groups.json emojis.json badges.json categories.json languages.json
```

### Custom django commands

#### `manage.py create_invite`

Creates a user invite and outputs its token.
Required for creating a new account.

```bash
usage: manage.py create_invite [-h] [--email EMAIL] [--username USERNAME] [--name NAME] [--badge BADGE]
```

#### `manage.py import_invites`

Imports user invites from a kickstarter/indiegogo csv

```bash
usage: manage.py import_invites [-h] [--indiegogo PATH_TO_CSV] [--kickstarter PATH_TO_CSV]
```

#### `manage.py reset_invite_email_boolean`

Resets invite_email_sent boolean for un-used invites created in the last --days

```bash
usage: manage.py reset_invite_email_boolean [-h] [--days DAYS]
```


#### `manage.py send_invites`

Send invite emails to all user invites who have not been sent the email. 

```bash
usage: manage.py send_invites [-h]
```

####`manage.py allocate_invites`

Assign user invites to all or specific users. 

```bash
usage: manage.py allocate_invites [-h] [--count INCREMENT_INVITES_BY_COUNT --limit [INVITE_COUNT_UPPER_LIMIT]] [--total TOTAL_INVITE_COUNT_TO_SET] [--username USERNAME]
```
*`--limit` works only with `--count`

#### `manage.py create_post_media_thumbnails`

Creates media_thumbnail, media_height and media_width for items which don't have it using the Post -> PostMedia relationship.

The command was created as a one off migration tool.

```bash
usage: manage.py create_post_media_thumbnails
```

#### `manage.py migrate_post_images`

Migrates Post -> PostImage to Post -> PostMedia -> PostImage.

The command was created as a one off migration tool.

#### `manage.py import_proxy_blacklisted_domains`

Import a list of domains to be blacklisted when calling the `ProxyAuth` and `ProxyDomainCheck` APIs.

```bash
usage: manage.py import_proxy_blacklisted_domains [--file The path to the file with the domains to import]
```

##### Example

```bash
python manage.py import_proxy_blacklisted_domains --file ./openbook_common/misc/domain_blacklists/porn/domains
```

#### `manage.py flush_proxy_blacklisted_domains`

Flush all of the blacklisted proxy domains

```bash
usage: manage.py flush_proxy_blacklisted_domains
```

#### `manage.py worker_health_check`

A a Django management command available for checking the worker health: 

Each queue has a required configurable `treshold`. These are configured in the Django settings.
The `FAILED_JOB_THRESHOLD` is the maximum amount of failed jobs that are allowed, before an alert is sent using the `openbook_common.helpers.send_alert_to_channel` command, which sends an alert to a monitoring channel on i.e. Slack. Using the `ALERT_HOOK_URL` option in the Django settings file, it is possible to add the Slack hook URL.

Other thresholds that are included are `ACTIVE_JOB_THRESHOLD` and `ACTIVE_WORKER_THRESHOLD`. Just as with the limit on failed jobs, there is an active job and worker limit too.

In `openbook_common.utils.rq_helpers` there is also a `FailedRQJobs` class, which has a function for removing failed jobs from the queue.

It is recommended to schedule the worker monitoring functions, to run at a 5 minute interval using `crontab`. Please DO NOT run the job as the root user.


#### Crowdin translations update
Download the latest django.po files in the respective locale/ folders from crowdin. 
Then locally run all or some of these commands depending on which models need updating.
It will update the `.json` files, then check them in.
```$xslt
./manage.py shell < openbook_common/i18n/update_translations_emoji_groups.py
./manage.py shell < openbook_common/i18n/update_translations_emojis.py
./manage.py shell < openbook_moderation/i18n/update_translations.py
./manage.py shell < openbook_categories/i18n/update_translations.py
```

## Available Django jobs

To schedule a job, go to the `/admin/scheduler` route on the running webserver.

The available jobs are

### openbook_posts.jobs.flush_draft_posts

Cleans up all draft posts which have not being modified for a day.

Should be run every hour or so.

### openbook_posts.jobs.curate_top_posts

Curates the top posts, which end up in the explore tab.

Should be run every 5 minutes or so.


### openbook_posts.jobs.clean_top_posts

Cleans the top posts which should no longer be top posts.

This happens if an item is soft deleted, reported and approved

Should be run every 5 minutes or so.


## Translations

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


## FAQ

### Double logging in console

The local development server runs a separate process for the auto-reloader. You can turn off the auto-reload process by passing the --noreload flag.

````bash
python manage.py runserver --noreload
````


#### Happy coding 🎉!

