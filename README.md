django-simple-import
====================

An import tool easy enough your users could use it. django-simple-import aims to keep track of logs 
and user preferences in the database. 

Project is now stable and feature complete. Of course it's always a good idea to test before deploying.

[Support development on gittip](http://www.gittip.com/bufke)

[![Build Status](https://travis-ci.org/burke-software/django-simple-import.png?branch=master)](https://travis-ci.org/burke-software/django-simple-import)

![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/start_import.png)
![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/match_columns.png)
![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/do_import.png)

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

1. pip install django-simple-import
1. Add 'simple_import' to INSTALLED APPS
1. Add simple_import to urls.py like
urlpatterns += url(r'^simple_import/', include('simple_import.urls')),
1. syncdb (you may use south)

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

If you need any help, we do consulting and custom development. Just email us at david at burkesoftware.com.
   

## Usage

Go to /simple_import/start_import/ or use the admin interface.

The screenshots have a django-grappelli like theme. The base templates have no style and are very basic. 
See an example of customization [here](https://github.com/burke-software/django-sis/tree/master/templates/simple_import).

There is also a log of import records. Check out /admin/simple_import/.

## Odd Things

Added a special set password property on auth.User to set password. This sets the password instead of just
saving a hash.

User has some required fields that...aren't really required. Hardcoded to let them pass.

### Security
I'm working on the assumption staff users are trusted. Only users with change permission 
to a field will see it as an option. I have not spent much time looking for ways users could
manipulate URLs to run unauthorized imports. Feel free to contribute changes.
All import views do require admin "is staff" permission.
