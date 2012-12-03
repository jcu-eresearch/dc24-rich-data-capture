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


Editing Schemas
---------------

Schema attributes for working with ColanderAlchemy have been made to work as following:
 * All ca_xxx attributes have the ca_ removed from the start and are added to the generated schema node
 * ca_group_xxx attributes create a MappingSchema surrounding the nodes from ca_group_start to ca_group_end, any ca_group_xxx
   attribute is added to the MappingSchema (eg. description) - ca_group_collabsed indicates if the MappingSchema should be collapsible and if it is currently collapsed.
 * ca_placeholder is used for initial greyed out text that disappears when clicked.
 * The ca_page attribute can be added to the SQLAlchemyMapping and ColanderAlchemy nodes to specify which page each node goes on for multi-page forms.
 * The ca_force_required attribute can be added to make the generated deform schema node be required without needing to add the ColanderAlchemy nullable attribute (which makes the database column not nullable)
 * The convert_schema method has been created to make the above notes work without alterning the base ColanderAlchemy code.

