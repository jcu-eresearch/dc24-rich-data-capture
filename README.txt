jcu.dc24.provisioning README
==================

Getting Started
---------------

- cd <directory containing this file>

- $venv/bin/python setup.py develop

- $venv/bin/initialize_jcu.dc24.provisioning_db development.ini

- $venv/bin/pserve development.ini

- Configure teh development.ini/production.ini pyramid_deform.tempdir to the desired temp folder
- Setup a cron job or equivalent to remove old files (eg. daily).

