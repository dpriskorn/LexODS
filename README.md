# LexODS
Add ODS identifier to Wikidata Lexemes (no property proposed yet). 

This script is maybe not that useful to run for anyone else besides the author in its current form. It is shared here to help others get started writing scripts to improve Wikidata.

It would be interesting to edit it to monitor the ODS website for newly published articles/words.

This script can easily be modified to create new lexemes for every word found in the list from ODS. Unfortunately that is not legal because of the database protection law and maybe local copyright laws too.

## Requirements
* wikibaseintegrator

Install using pip:
`$ sudo pip install -r

If pip fails with errors related to python 2.7 you need to upgrade your OS. E.g. if you are using an old version of Ubuntu like 18.04.

## Getting started
To get started install the following libraries with your package manager or
python PIP:
* wikibaseintegrator

Please create a bot password for running the script for
safety reasons here: https://www.wikidata.org/wiki/Special:BotPasswords

Copy config.example.py to config.py yourself and adjust the following
content:

username = "username"
password= "password"

# License
Everything is under GPLv3+, see the LICENSE file. 

# Credit
Author: Dennis Priskorn 2021