jcu.dc24.provisioning README
==================

Getting Started
---------------
Either of these methods will work, buildout is provided for integration with ingesterapi and ingesterplatform for JCU's development environment:

With buildout:
1. Install python 2.7
2. Install easy_install + easy_install virtualenv
3. Setup git so that it is runnable from the command line - On windows:
	- Install msysgit 
	- Add to path variable as <installdir>\cmd
	- Install tortiosegit 
	- Ensure git works from the command line, cross your fingers..., if all else fails use a git-bash command prompt.
4. Create venv from python 2.7 (<python27>/Scripts/virtualenv --no-site-packages <location>)
5. Make sure the virtual env is configured with a valid c compiler - On windows this will probably involve:
	- Install mingw
	- Add <installdir>/bin and <installdir>/mingw32/bin to path
	- Add [build] compiler=mingw32 to venv/lib/distutils/distutils.cfg
	- Delete all -mno-cygwin within c:/python27/libs/distutils/cygwincompiler.py
6. Activate created virtual env
7. Checkout this git branch 
8. <venv>/python ./bootstrap.py - Use the fully qualified path - activate is buggy...
9. <venv>/python ./bin/buildout-script.py - Use the fully qualified path - activate is buggy...


Without buildout:
1. Update the development.ini example with your configurations, areas that must be configured are shown as <something>
2. cd <directory containing this file>
3. $venv/bin/python setup.py develop
4. $venv/bin/pserve ../../development.ini 

Note: Windows uses scripts instead of bin

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


Developing in an IDE
--------------------
IDE support seems to be limited and can be difficult to get working
* Setup and install following the above steps + information from the internet so that you can run the application from a command line (eg. in the virtualenv activate then run)
* If possible add a pre-run executable to run activate/activate.bat/activate-this.py
* Add $venv/bin/site-packages as both classes and sources libraries
* If it still doesn't work, try adding execfile(".../activate_this.py", dict(__file__=".../activate_this.py")) to the lowest level init file.