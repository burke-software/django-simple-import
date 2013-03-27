django-simple-import
====================

An import tool easy enough your users could use it. django-simple-import aims to keep track of logs 
and user preferences in the database. 

1.0 has been released to pypi

Project is minimally functional. Please evaluate before using in Production. Expect more features soon.

![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/start_import.png)
![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/match_columns.png)
![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/do_import.png)

## Features
- Supports csv, xls, xlsx, and ods import file
- Save user matches of column headers to fields
- Guess matches
- Create, Update, or do both imports
- Allow programmers to define special import properties for custom handling (not implemented)
- Set related objects by any unique field (not implemented)
- Simulate imports before commiting to database
- Undo (create only) imports
- Security checks if user has correct permissions (partially implemented)

## Install

1. pip install django-simple-import
1. Add 'simple_import' to INSTALLED APPS
1. Add simple_import to urls.py like
urlpatterns += url(r'^simple_import/', include('simple_import.urls')),
1. syncdb (you may use south)
1. (Optional) define allowed methods to be "imported". Example:
class Foo(models.Model):
    ...
    def set_bar(self, value):
        self.bar = value
    simple_import_methods = ('set_bar',)
   

## Usage

Go to /simple_import/start_import/ or use the admin interface

In the screenshots I gave them a django-grappelli theme. The base templates have no style and are very basic. 
See example of customization [here](https://github.com/burke-software/django-sis/tree/master/templates/simple_import)

### Security
I'm working on the assumtion staff users are trusted. Only users with change permission 
to a field will see it as an option. But I have not spent much time looking for ways users could
manipulate urls to run unauthorized imports. Feel free to contribute if this is a need you have.
All import views do require admin "is staff" permission.
