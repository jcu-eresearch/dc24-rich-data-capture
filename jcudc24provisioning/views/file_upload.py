import binascii
import colander
from pyramid_deform import chunks, string_types, _marker
import deform
import os
from deform.widget import FileUploadWidget, filedict

__author__ = 'casey'


class ProvisioningUploadTempStore(object):
    def __init__(self, request, directory):
        self.dir = os.path.normpath(directory) + os.sep
        self.request = request
        self.session = request.session
        self.tempstore = self.session.setdefault('directory_upload.tempstore', {})

    def preview_url(self, name):
        return self._get_file_path(name, self.get(name)['filename'])

    def __contains__(self, name):
        return self.get(name) is not None

    def __setitem__(self, name, data):
        newdata = data.copy()
        stream = newdata.pop('fp', None)

        if stream is not None:
            # TODO: This possibly leaves it open for 2 uers to change files at the same time!
            newdata['filepath'] = self._get_file_path(os.path.normpath(name), data['filename'])
            fp = open(newdata['filepath'], 'w+b')

            for chunk in chunks(stream):
                fp.write(chunk)

        self.tempstore[name] = newdata
        self.session.changed()

    def _get_file_path(self, name, filename):
        return "%s.%s" % (self._get_base_path(name), filename)

    def _get_base_path(self, name):
        return self.dir + name

    def get(self, name, default=None):
        data = self.tempstore.get(name)

        new_data = None
        if data is None and name is not None and name:
            uid = name
            if os.sep in name:
                name = os.path.normpath(name)
                filepath = name.replace(self.dir, "")
                uid, filename = filepath.split(".", 1)

            files = os.listdir(self.dir)
            for file in files:
                if uid in file:
                    uid, filename = file.replace(self.dir, "").split(".", 1)
                    new_data = {
                        "filename": filename,
                        "filepath": self.dir + file,
                        "preview_url": self.dir + file,
                        "uid": uid
                    }
                    break
        else:
            new_data = data.copy()

        if new_data is None:
            return default

        filepath = new_data.get('filepath')

        if filepath is not None:
            try:
                new_data['fp'] = open(filepath, 'rb')
            except IOError:
                pass

        return new_data

    def __getitem__(self, name):
        data = self.get(name, _marker)
        if data is _marker:
            raise KeyError(name)
        return data


class ProvisioningFileUploadWidget(FileUploadWidget):
    def serialize(self, field, cstruct, **kw):
        if cstruct in (colander.null, None):
            cstruct = {}

        if isinstance(cstruct, basestring):
            cstruct = self.tmpstore.get(cstruct)

        if cstruct:
            uid = cstruct['uid']
            if not uid in self.tmpstore:
                self.tmpstore[uid] = cstruct

        readonly = kw.get('readonly', self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null

        if not isinstance(pstruct, dict):
            pstruct = self.tmpstore.get(pstruct)
            if pstruct is None:
                return colander.null

        upload = pstruct.get('upload')
        uid = pstruct.get('uid')

        if hasattr(upload, 'file'):
            # the upload control had a file selected
            data = filedict()
            data['fp'] = upload.file
            filename = upload.filename
            # sanitize IE whole-path filenames
            filename = filename[filename.rfind('\\')+1:].strip()
            data['filename'] = filename
            data['mimetype'] = upload.type
            data['size']  = upload.length
            if uid is None:
                # no previous file exists
                while 1:
                    uid = self.random_id()
                    if self.tmpstore.get(uid) is None:
                        data['uid'] = uid
                        self.tmpstore[uid] = data
                        preview_url = self.tmpstore.preview_url(uid)
                        data['preview_url'] = preview_url
                        self.tmpstore[uid]['preview_url'] = preview_url
                        break
            else:
                # a previous file exists
                data['uid'] = uid
                self.tmpstore[uid] = data
                preview_url = self.tmpstore.preview_url(uid)
                self.tmpstore[uid]['preview_url'] = preview_url
        else:
            # the upload control had no file selected
            if uid is None or not uid:
                # no previous file exists
                return colander.null
            else:
                # a previous file should exist
                data = self.tmpstore.get(uid)
                data['preview_url'] = data['filepath']
                # but if it doesn't, don't blow up
                if data is None:
                    return colander.null

        return data['preview_url']



@colander.deferred
def upload_widget(node, kw):
    request = kw['request']
    tmp_store = ProvisioningUploadTempStore(request, request.registry.settings.get("workflows.files"))
    widget = ProvisioningFileUploadWidget(tmp_store)
    return widget


class Attachment(colander.SchemaNode):
    def __init__(self, typ=deform.FileData(), *children, **kw):
        if not "widget" in kw: kw["widget"] = upload_widget
        if not "title" in kw: kw["title"] = "Attach File"
        colander.SchemaNode.__init__(self, typ, *children, **kw)