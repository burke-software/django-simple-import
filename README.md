django-simple-import
====================

An import tool easy enough your users could use it. django-simple-import aims to keep track of logs 
and user preferences in the database. 

Project is now stable and feature complete. Of course it's always a good idea to test before deploying.

![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/start_import.png)
![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/match_columns.png)
![Alt text](https://raw.github.com/burke-software/django-simple-import/master/docs/do_import.png)

## Features
- Supports csv, xls, xlsx, and ods ([Warning: ods support is poor](https://github.com/burke-software/django-simple-import/issues/10)) import file
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
1. (Optional) define allowed methods to be "imported". Example:

    class Foo(models.Model):
        ...
        def set_bar(self, value):
            self.bar = value
        simple_import_methods = ('set_bar',)
        
If you need any help we do consulting and custom development. Just email us at david at burkesoftware.com.
   

## Usage

Go to /simple_import/start_import/ or use the admin interface

In the screenshots I gave them a django-grappelli theme. The base templates have no style and are very basic. 
See example of customization [here](https://github.com/burke-software/django-sis/tree/master/templates/simple_import)

There is also a log of import records. Check out /admin/simple_import/

### Security
I'm working on the assumtion staff users are trusted. Only users with change permission 
to a field will see it as an option. I have not spent much time looking for ways users could
manipulate urls to run unauthorized imports. Feel free to contribute changes.
All import views do require admin "is staff" permission.
