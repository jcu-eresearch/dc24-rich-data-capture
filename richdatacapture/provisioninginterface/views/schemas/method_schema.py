import colander
import deform
from richdatacapture.provisioninginterface.views.workflow.workflows import MemoryTmpStore

__author__ = 'Casey Bajema'

types = (('form', 'Web Form (Simple form generator or help request)'),
         ('file_stream', 'File Stream (Video, audio, sensor data, etc.)'),
         ('file_upload', 'File Upload (Sensor, CSV, Binary data, etc.)'),
         ('sensor', 'Sensor Stream - Sensors must implement SOS'))

class Attachment(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), default="")
    attachment = MemoryTmpStore()
    attachFile = colander.SchemaNode(deform.FileData(), title="Attach File", missing=attachment)

class Attachments(colander.SequenceSchema):
    attachment = Attachment(widget=deform.widget.MappingWidget(template="inline_mapping"))

class WebsiteSchema(colander.SequenceSchema):
    website = colander.SchemaNode(colander.String())

class DataSource(colander.Schema):
    dataType = colander.SchemaNode(colander.String(), title="Method Type",
        widget=deform.widget.SelectWidget(values=types)
        , validator=colander.OneOf(['form', 'file_stream', 'file_upload', 'sensor']),
        description="The selected type of input method defines how your project will provide data."\
                    "<ul>"\
                    "<li><b>Web Form: </b>Use a simple form generator (or request help) for an online form accessible through this interface.</li>"\
                    "<li><b>File Stream: </b>Setup automatic Push or Pull of files from a URL location.  Push is where an external system sends files, Pull is where this system polls the provided URL for files.  Both methods must have the correct file type and follow the naming convention.<li>"\
                    "<li><b>File Upload: </b>Users manually upload files using a form on this system.</li>"\
                    "<li><b>Sensor Stream: </b>Set-up a sensor that implements the Sensor Observation Service (SOS) to push data into this systems SOS server.</li>"\
                    "</ul>",
        default="Select the easiest method for your project.  If all else fails, manual file uploads will work for all data types.")

    name = colander.SchemaNode(colander.String(),
        default="Searchable identifier for this input method (eg. Invertebrate observations)",
        description="Descriptive, human readable name for this input method.  The name will be used to select this method in the <i>Datasets</i> step and will also be searchable within the database.")
    description = colander.SchemaNode(colander.String(), title="Description", widget=deform.widget.TextAreaWidget(),
        description="Provide a description of this method, this should include what, why and how the data is being collected but <b>Dont enter where or when</b> this method will be used as this is information relevant to the dataset, not the method."
        ,
        default="Enter specific details for this method, users of your data will need to know how reliable your data is and how it was collected.")
    url = WebsiteSchema(title="Further information (URL)", description="If there are web addresses that can provide more information on your data collection method add them here.  Examples may include manufacturers of your equipment or an article on the calibration methods used.")
    attachments = Attachments(missing="", description="Attach information about this method, this is preferred to external URLs as it is more reliable.  Example attachments would be sensor datasheets, documentation describing your file/data storage schema or calibration data.")
    storage = colander.SchemaNode(colander.String(), title="Storage schema - todo",
        default="Only for files - others are known", description="<b>Need to update when schemas are fully worked out!</b>")
