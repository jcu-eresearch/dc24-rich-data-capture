#Copyright (c) 2012, James Cook University All rights reserved.
#
#Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#3.  Neither the name of James Cook University nor the names of its contributors
#    may be used to endorse or promote products derived from this software without
#    specific prior written permission.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import sys
from jcudc24provisioning.models import DBSession
from jcudc24provisioning.models.project import Attachment, MethodAttachment
import os
from pyramid.paster import get_appsettings
from sqlalchemy import engine_from_config

__author__ = 'Casey Bajema'


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s production.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    cleanup_uploads(config_uri)

def cleanup_uploads(config_uri):
    settings = get_appsettings(config_uri)

    # Initialise the database connection.
    engine = engine_from_config(settings, 'sqlalchemy.', pool_recycle=3600)
    DBSession.configure(bind=engine)
    session = DBSession()

    uploads_folder = settings.get("workflows.files")
    if not os.path.exists(uploads_folder):
        raise ValueError("The provided EnMaSSe file uploads directory doesn't exist!")
        sys.exit(1)
    if not os.path.isdir(uploads_folder):
        raise ValueError("The provided uploads address isn't a directory!")
        sys.exit(1)

    for f_name in os.listdir(uploads_folder):
        if session.query(Attachment).filter_by(attachment=f_name).count() + \
           session.query(MethodAttachment).filter_by(attachment=f_name).count() == 0:
            os.remove(f_name)

