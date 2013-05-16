import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',              # BSD-derived Repoze Public License. (Good)
    'SQLAlchemy',           # MIT (Good)
    'transaction',          # ZPL 2.1 (Good)
    'pyramid_tm',           # Non-standard (Good)
    'pyramid_debugtoolbar', # Non-standard (Good)
    'zope.sqlalchemy',      # ZPL 2.1 (Good)
    'waitress',             # ZPL 2.1 (Good)
    'deform',               # 3 clause BSD/Non-standard (Good)
    'colander >= 1.0a1',    # Non-standard (Good)
    'pyramid_deform',       # Non-standard (Good)
    "pyramid_beaker",       # Non-standard (Good)
    "mysql-python",         # GPL License 2.0
    'webob',                # MIT
    'paramiko',             # GPL 2.1 (Good)
    'requests',             # Apache2
    'hashlib',              # Python software foundation license V2 (good)
    'pyramid_fanstatic',    # MIT
    'js.deform',            # BSD
    'js.jquery',            # BSD
    'js.jqueryui',          # BSD
]

setup(name='jcu.dc24.provisioning',
      version='0.0',
      license="BSD 3-Clause",
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
      [fanstatic.libraries]
      jcudc24provisioning = jcudc24provisioning.resources:library
      """,
      requires=['colander', "deform", "pyramid_deform", "pyramid_beaker", "pyramid", "transaction", "sqlalchemy", "webob",
                     "colanderalchemy"],
      )

