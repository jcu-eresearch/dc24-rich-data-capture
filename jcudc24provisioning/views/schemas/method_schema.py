import colander
import deform
from jcudc24provisioning.views.schemas.common_schemas import WebsiteSchema, Attachment, OneOfDict

__author__ = 'Casey Bajema'

class OptGroup():
    pass

data_types = (
    ('video', 'Video'),
    ('audio', 'Audio'),
    ('temperature', 'Temperature'),
    ('humidity', 'Humidity'),
    ('rain_fall', 'Rain fall'),
    ('moisture', 'Moisture'),
    ('wind', 'Wind (direction & speed)'),
    ('weight', 'Weight'),
    ('light_intensity', 'Light intensity'),
    ('file', 'File (Generic file that doesn\'t have a type defined)'),
    ('custom', 'Web Form/Custom (No defined type, describe with custom fields)'),
)

data_sources = (
    ('manual', 'Web Form/Manual (Add data using this website only)'),
    ('pull', 'Poll external filesystem'),
    ('push', 'Push to this website through the API (advanced)'),
    ('sos', 'Sensor Observation Service (SOS)')
)

field_types = (
    ('text_input', 'Single line text'),
    ('text_area', 'Multi-line text'),
    ('checkbox', 'Checkbox'),
    ('select', 'Select/Dropdown box'),
    ('select', 'Radio buttons/Multiple choice'),
    ('file', 'File upload'),
    ('website', 'Website'),
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('address', 'Address'),
    ('person', 'Person'),
)

class InformationAttachment(colander.MappingSchema):
     attachment = Attachment()
     note = colander.SchemaNode(colander.String(), placeholder="eg. Sensor data sheet")

class Attachments(colander.SequenceSchema):
     attachment = InformationAttachment(widget=deform.widget.MappingWidget(template="inline_mapping"))

class CustomField(colander.MappingSchema):
    data_type = colander.SchemaNode(colander.String(), title="Field Type",
        widget=deform.widget.SelectWidget(values=field_types),
        description="",
        placeholder="Type of field that should be shown.")
    field_name = colander.SchemaNode(colander.String(), title="Name", placeholder="eg. Temperature")
    description = colander.SchemaNode(colander.String(), title="Desc.", placeholder="eg. Calibrated temperature reading")
    placeholder = colander.SchemaNode(colander.String(), title="Example", placeholder="eg. 26.3")
    validators = colander.SchemaNode(colander.String(), title="Validator", placeholder="eg. Numerical value with decimal places")
    notes = colander.SchemaNode(colander.String(), title="Admin Notes", placeholder="eg. Please read this field from the uploaded files, it will follow a pattern like temp:xxx.xx")


class CustomFieldsSchema(colander.SequenceSchema):
    field = CustomField(title="Custom Fields",# widget=deform.widget.MappingWidget(template="inline_mapping"),
        description="")

class Method(colander.Schema):
    data_type = colander.SchemaNode(colander.String(), title="Data Type",
        widget=deform.widget.SelectWidget(values=data_types),
        description="The type of data that is being collected, if your data doesn\\'t fit any of the available types select " \
                    "Web Form/Custom and use the custom fields below to generate the required schema.",
        placeholder="Type of data being collected.")
    data_source = colander.SchemaNode(colander.String(), title="Data Source",
        widget=deform.widget.SelectWidget(values=data_sources),
        description="How does the data get transferred into this system?"\
                    "<ul>"\
                    "<li><b>Web Form: </b>Use a simple form generator (or request help) for an online form accessible through this interface.</li>"\
                    "<li><b>File Stream: </b>Setup automatic Push or Pull of files from a URL location.  Push is where an external system sends files, Pull is where this system polls the provided URL for files.  Both methods must have the correct file type and follow the naming convention.<li>"\
                    "<li><b>File Upload: </b>Users manually upload files using a form on this system.</li>"\
                    "<li><b>Sensor Stream: </b>Set-up a sensor that implements the Sensor Observation Service (SOS) to push data into this systems SOS server.</li>"\
                    "</ul>",
        placeholder="Select the easiest method for your project.  If all else fails, manual file uploads will work for all data types.")

    name = colander.SchemaNode(colander.String(),
        placeholder="Searchable identifier for this input method (eg. Invertebrate observations)",
        description="Descriptive, human readable name for this input method.  The name will be used to select this method in the <i>Datasets</i> step and will also be searchable within the database.")
    description = colander.SchemaNode(colander.String(), title="Description", widget=deform.widget.TextAreaWidget(),
        description="Provide a description of this method, this should include what, why and how the data is being collected but <b>Don\'t enter where or when</b> as this is information relevant to the dataset, not the method."
        ,
        placeholder="Enter specific details for this method, users of your data will need to know how reliable your data is and how it was collected.")
    url = WebsiteSchema(title="Further information (URL)", description="If there are web addresses that can provide more information on your data collection method add them here.  Examples may include manufacturers of your equipment or an article on the calibration methods used.")
    attachments = Attachments(missing="", description="Attach information about this method, this is preferred to external URLs as it is more reliable.  Example attachments would be sensor datasheets, documentation describing your file/data storage schema or calibration data.")
    custom_fields = CustomFieldsSchema(title="Custom Fields", description="Provide details of the schema that this input" \
                                                                         "method requires to store it\\'s data along with " \
                                                                         "descriptions for the manual data entry form and" \
                                                                         "further notes to the administrators.")
