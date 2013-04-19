import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'zope.sqlalchemy',
    'waitress',
    'deform',
    'colander >= 1.0a1',
    'pyramid_deform',
    "pyramid_beaker",
    "mysql-python",
    'webob',
    'paramiko',
    'requests',
    'hashlib',
#    'pyramid_fanstatic',
#    'js.deform',
#    'js.jquery',
#    'js.jqueryui',
]

setup(name='jcu.dc24.provisioning',
      version='0.0',
      description='jcu.dc24.provisioning',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Casey Bajema',
      author_email='casey@bajtech.com.au',
      url='http://www.bajtech.com.au',
      keywords='research data rda tdh ands web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='jcudc24provisioning',
      install_requires=requires,
      setup_requires=[
        'setuptools-git',
        ],
      entry_points="""\
      [paste.app_factory]
      main = jcudc24provisioning:main
      [console_scripts]
      initialize_jcu.dc24.provisioning_db = jcudc24provisioning.scripts.initializedb:main
      """,
      requires=['colander', "deform", "pyramid_deform", "pyramid_beaker", "pyramid", "transaction", "sqlalchemy", "webob",
                     "colanderalchemy"],
      )

