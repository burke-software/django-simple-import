django-simple-import
====================

An import tool easy enough your users could use it. django-simple-import aims to keep track of logs
and user preferences in the database.

Project is now stable and feature complete. Of course it's always a good idea to test before deploying.

[![Build Status](https://travis-ci.org/burke-software/django-simple-import.png?branch=master)](https://travis-ci.org/burke-software/django-simple-import)
[![Coverage Status](https://coveralls.io/repos/burke-software/django-simple-import/badge.svg?branch=master&service=github)](https://coveralls.io/github/burke-software/django-simple-import?branch=master)

![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/start_import.png)
![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/match_columns.png)
![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/do_import.png)

# Changelog

## 2.0

2.0 adds support for Django 1.9 and 1.10. Support for 1.8 and under is dropped. Support for Python 2 is dropped. 
Use 1.x for older environments.

## 1.17

The most apparent changes are 1.7 compatibility and migration to Django's
atomic transactions. Please report any issues. I test against mysql innodb, postgres, and sqlite.

## Features
- Supports csv, xls, xlsx, and ods import file
- Save user matches of column headers to fields
- Guess matches
- Create, update, or both
- Allow programmers to define special import methods for custom handling
- Support for [django-custom-field](https://github.com/burke-software/django-custom-field)
- Set related objects by any unique field
- Simulate imports before commiting to database
- Undo (create only) imports
- Security checks if user has correct permissions (partially implemented)

## Install

1. `pip install django-simple-import`
2. Add 'simple_import' to INSTALLED APPS
3. Add simple_import to urls.py like
`url(r'^simple_import/', include('simple_import.urls')),`
4. migrate

## Optional Settings
Define allowed methods to be "imported". Example:

    class Foo(models.Model):
        ...
        def set_bar(self, value):
            self.bar = value
        simple_import_methods = ('set_bar',)

### settings.py
SIMPLE_IMPORT_LAZY_CHOICES: Default True. If enabled simple_import will look up choices when importing. Example:

    choices  = ['M', 'Monday']

If the spreadsheet value is "Monday" it will set the database value to "M."

SIMPLE_IMPORT_LAZY_CHOICES_STRIP: Default False.  If enabled, simple_import will trip leading/trailing whitespace 
from the cell's value before checking for a match.  Only relevant when SIMPLE_IMPORT_LAZY_CHOICES is also enabled.
 
If you need any help, we do consulting and custom development. Just email us at david at burkesoftware.com.


## Usage

Go to `/simple_import/start_import/` or use the admin interface.

The screenshots have a django-grappelli like theme. The base templates have no style and are very basic.
See an example of customization [here](https://github.com/burke-software/django-sis/tree/master/templates/simple_import).
It is often sufficient to simply override `simple_import/templates/base.html`.

There is also a log of import records. Check out `/admin/simple_import/`.

## Odd Things

Added a special set password property on auth.User to set password. This sets the password instead of just
saving a hash.

User has some required fields that...aren't really required. Hardcoded to let them pass.

### Security

I'm working on the assumption staff users are trusted. Only users with change permission
to a field will see it as an option. I have not spent much time looking for ways users could
manipulate URLs to run unauthorized imports. Feel free to contribute changes.
All import views do require admin "is staff" permission.

## Testing

If you have [docker-compose](https://docs.docker.com/compose/) and [Docker](https://www.docker.com/)
installed, then just running `docker-compose run --rm app ./manage.py test` will do everything you need to test
the packages.

Otherwise look at the `.travis.yml` file for test dependencies.
