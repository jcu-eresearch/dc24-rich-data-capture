"""
Class that wraps all functionality to transfer files over SFTP (File transfer over SSH) used for exporting metadata
records to ReDBox.
"""

import hashlib

__author__ = ("Casey Bajema", 'ccpizza (http://code.activestate.com/recipes/576810-copy-files-over-ssh-using-paramiko/)')

import logging
logger = logging.getLogger(__name__)


## {{{ http://code.activestate.com/recipes/576810/ (r20)
#!/usr/bin/env python

## Copy files unattended over SSH using a glob pattern.
## It tries first to connect using a private key from a private key file
## or provided by an SSH agent. If RSA authentication fails, then
## password login is attempted.

##
## DEPENDENT MODULES:
##      * paramiko, install it with `easy_install paramiko`

## NOTE: 1. The script assumes that the files on the source
##       computer are *always* newer that on the target;
##       2. no timestamps or file size comparisons are made
##       3. use at your own risk

import os
import glob
import paramiko

class SFTPFileSend(object):
    """
    Wraps functionality to transfer files over SFTP (File transfer over SSH).
    """
    transport = None
    sftp = None

    def __init__(self, hostname, port, username, password=None, rsa_private_key=None):
        """
        Intialise the SFTP connection parameters, this allows for authentication with either a key or username/password.

        :param hostname: SSH Host address
        :param port: SSH connection port
        :param username: SSH authentication username (only required if a private key isn't provided)
        :param password: SSH password for either the private key or the username (key takes precedence)
        :param rsa_private_key: Private key to authenticate the SSH connection (a username/password can be used instead).
        :return:
        """
        self.username = username
        self.password = password
        self.rsa_private_key = rsa_private_key
        self.hostname = hostname
        self.port = int(port)

        # get host key, if we know one
        hostkeytype = None
        hostkey = None
        files_copied = 0
        try:
            host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except IOError:
            try:
                # try ~/ssh/ too, e.g. on windows
                host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
            except IOError:
                logger.warning('*** Unable to open host keys file')
                host_keys = {}

        if host_keys.has_key(hostname):
            hostkeytype = host_keys[hostname].keys()[0]
            hostkey = host_keys[hostname][hostkeytype]
            logger.info('Using host key of type %s' % hostkeytype)

        try:
            logger.info('Establishing SSH connection to: %s:%s' % (hostname, port))
            self.transport = paramiko.Transport((hostname, int(port)))
            self.transport.start_client()

            try:
                if rsa_private_key is not None:
                    self._ssh_agent_auth()
            except Exception, e:
                logger.warning('RSA key auth failed!')
                try:
                    self.transport.close()
                except:
                    pass

            if not self.transport.is_authenticated():
                logger.warning('Trying password login...')
                self.transport = paramiko.Transport((hostname, port))
                self.transport.connect(username=username, password=password, hostkey=hostkey)
            else:
                self.sftp = self.transport.open_session()

            # now, connect and use paramiko Transport to negotiate SSH2 across the connection
            if not isinstance(self.sftp, paramiko.SFTPClient):
                self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        except Exception, e:
           logger.exception('Failed to connect to the remote host!')
           try:
               self.transport.close()
           except:
               pass

    def _ssh_agent_auth(self):
        """
        Attempt to authenticate to the given transport using any of the private
        keys available from an SSH agent or from a local private RSA key file (assumes no pass phrase).
        """
        try:
            ki = paramiko.RSAKey.from_private_key_file(self.rsa_private_key, self.password)
        except Exception, e:
            logger.exception('Failed loading %s' % (self.rsa_private_key))

        agent = paramiko.Agent()
        agent_keys = agent.get_keys() + (ki,)
        if len(agent_keys) == 0:
            return

        for key in agent_keys:
            logger.info('Trying ssh-agent key %s' % key.get_fingerprint().encode('hex'))
            try:
                self.transport.auth_publickey(self.username, key)
                logger.info('... success!')
                return
            except paramiko.SSHException, e:
                logger.exception('... failed!')

    def upload_file(self, local_file, remote_file):
        """
        Upload a single file to the SFTP server.

        :param local_file: File to upload
        :param remote_file: Remote server file/folder to upload to.
        :return: True/False on success/failure respectively.
        """
        try:
            # dirlist on remote host
            #    dirlist = sftp.listdir('.')
            #    print "Dirlist:", dirlist

            # BETTER: use the get() and put() methods
            # for fname in os.listdir(dir_local):

            is_up_to_date = False

            #if remote file exists
            try:
                if self.sftp.stat(remote_file):
                    local_file_data = open(local_file, "rb").read()
                    remote_file_data = self.sftp.open(remote_file).read()
                    md1 = hashlib.new(local_file_data).digest()
                    md2 = hashlib.new(remote_file_data).digest()
                    if md1 == md2:
                        is_up_to_date = True
                        logger.info("Remote file exists and is identical: %s" % os.path.basename(local_file))
                    else:
                        logger.info("Remote file exists and is different: %s" % os.path.basename(local_file))
            except:
                logger.info("New file created: %s" % os.path.basename(local_file))

            if not is_up_to_date:
                logger.info('Copying %s to %s' % (local_file, remote_file))
                self.sftp.put(local_file, remote_file, confirm=True)
                return True # File was uploaded

        except Exception, e:
            logger.exception('*** Caught exception: %s: ' % (e.__class__))
#            try:
#                self.transport.close()
#            except:
#                return False
            return False
        logger.info("File uploaded: %s" % remote_file)

        return False # File wasn't uploaded, may have already been up to date or there may have been an error.
        ## end of http://code.activestate.com/recipes/576810/ }}}

    def upload_directory(self, local_dir, remote_dir, glob_pattern=None, extension=None):
        """
        Upload all files in local_dir to the remote_dir folder.

        :param local_dir: Folder to upload all files from.
        :param remote_dir: Remote directory to upload files into.
        :param glob_pattern: Glob match pattern to filter files to be uploaded from local_dir.
        :param extension:  If provided only files with this extension will be uploaded.
        :return: None
        """
        files_copied = 0

        try:
            # dirlist on remote host
            #    dirlist = sftp.listdir('.')
            #    print "Dirlist:", dirlist

            try:
#                self.sftp.chdir("~/")
#                test = self.sftp.getcwd()
                self.sftp.mkdir(remote_dir)
            except IOError, e:
                logger.info('(assuming %s exists' % remote_dir)


            if glob_pattern is None:
                glob_pattern = "*"

            for fname in glob.glob(local_dir + os.sep + glob_pattern):
                if extension is None or fname.lower().endswith(extension):
                    local_file = os.path.join(local_dir, fname)
                    remote_file = remote_dir + '/' + os.path.basename(fname)

                    if self.upload_file(local_file, remote_file):
                        files_copied += 1

        except Exception, e:
            logger.exception('*** Caught exception: %s: ' % (e.__class__))
#            try:
##                self.transport.close()
#            except:
#                pass
        logger.info('=' * 60)
        logger.info('Total files copied: %s' % str(files_copied))
        logger.info('All operations complete!')
        logger.info('=' * 60)
        ## end of http://code.activestate.com/recipes/576810/ }}}

    def close(self):
        """
        Close this SFTP connection, close should always be called when finished with the SFTPFilesend object.
        :return: None
        """
        if self.transport is not None:
            self.transport.close()
