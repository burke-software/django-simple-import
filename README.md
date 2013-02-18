django-simple-import
====================

An import tool easy enough your users could use it. django-simple-import aims to keep track of logs 
and user preferences in the database. 

Project is not yet stable, do not use in production.

## Features
- Supports csv, xls, xlsx, and ods import file
- Save user matches of column headers to fields
- Guess matches and allow programmers to give alternative names (partially implimented)
- Create, Update, or do both imports (partially implimented)
- Allow programmers to define special import properties for custom handling (not implimented)
- Set related objects by any unique field (not implimented)
- Simulate imports before commiting to database
- Undo (create only) imports
- Security checks if user has correct permissions (partially implimented)

## Install

## Usage


### Security
I'm working on the assumtion you staff users are trusted. Only users with change permission 
to a field will see it as an option. But I have not spent much time looking for ways users could
manipulate urls to run unauthorized imports. Feel free to contribute if this is a need you have.
All import views do require admin "is staff" permission.
