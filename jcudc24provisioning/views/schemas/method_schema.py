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
#    ('file', 'File (Generic file that doesn\'t have a type defined)'),
    ('custom', '(Advanced) No defined type'),
)

data_sources = (
    ('manual', 'Web Form/Manual (Add data using this website only)'),
    ('pull', 'Poll external file system'),
    ('push', '(Advanced) Push to this website through the API'),
    ('sos', 'Sensor Observation Service (SOS)'),
    ('dataset', '(Advanced) Output from other dataset'),
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
    ('hidden', 'Hidden (Used by custom processing only)'),
)

class InformationAttachment(colander.MappingSchema):
     attachment = Attachment()
     note = colander.SchemaNode(colander.String(), placeholder="eg. data sheet", widget=deform.widget.TextInputWidget(css_class="full_width"))

class Attachments(colander.SequenceSchema):
     attachment = InformationAttachment(widget=deform.widget.MappingWidget(template="inline_mapping"))

class CustomField(colander.MappingSchema):
    field_type = colander.SchemaNode(colander.String(), title="Field Type",
        widget=deform.widget.SelectWidget(values=field_types),
        description="",
        placeholder="Type of field that should be shown.")
    field_name = colander.SchemaNode(colander.String(), title="Name", placeholder="eg. Temperature", widget=deform.widget.TextInputWidget(css_class="full_width"))
    description = colander.SchemaNode(colander.String(), title="Description", placeholder="eg. Calibrated temperature reading", widget=deform.widget.TextInputWidget(css_class="full_width"))
    placeholder = colander.SchemaNode(colander.String(), title="Example", placeholder="eg. 26.3", widget=deform.widget.TextInputWidget(css_class="full_width"))
    default = colander.SchemaNode(colander.String(), title="Default Value.", placeholder="Use appropriately where the user will usually enter the same value.", widget=deform.widget.TextInputWidget(css_class="full_width"))
    validators = colander.SchemaNode(colander.String(), title="Validator", placeholder="eg. Numerical value with decimal places or what values are expected such as for a dropdown box", widget=deform.widget.TextInputWidget(css_class="full_width"))
    notes = colander.SchemaNode(colander.String(), title="Admin Notes", placeholder="eg. Please read this field from the uploaded files, it will follow a pattern like temp:xxx.xx", widget=deform.widget.TextAreaWidget(css_class="full_width"))


class CustomFieldsSchema(colander.SequenceSchema):
    field = CustomField(title="Custom Fields",# widget=deform.widget.MappingWidget(css_class="full_width"),
        description="")

class MethodTemplateSchema(colander.MappingSchema):
    copy_previous_method = colander.SchemaNode(colander.String(), widget=deform.widget.AutocompleteInputWidget(size=250, min_length=1, values=('Method A','Method B'), template="template_autocomplete_input"),
        placeholder="TODO: Autocomplete from previous projects methods (based on method name)")

class Method(colander.Schema):
    copy_previous_method = MethodTemplateSchema(title="Use a previously created method as a template",
            widget=deform.widget.MappingWidget(template="inline_mapping"),
            description="Use a previously created method as a template, <b>this will overwrite all fields on this page</b> " \
                        "with the content in the selected method.<br />" \
                        "Usage: If the same sensor is used for 2 projects you don't need to recreate the same method twice!")


    data_type = colander.SchemaNode(colander.String(), title="Data Type",
        widget=deform.widget.SelectWidget(values=data_types),
        description="The type of data that is being collected, additional information/fields can be added by extending the base data types using the custom fields below.</br></br>" \
                    "<b>Only select 'No defined type' if no other type is applicable.</b>",
        placeholder="Type of data being collected.")
    data_source = colander.SchemaNode(colander.String(), title="Data Source",
        widget=deform.widget.SelectWidget(values=data_sources),
        description="How does the data get transferred into this system?"\
                    "<ul>"\
                    "<li><b>Web Form/Manual: </b>Only use an online form accessible through this interface to manually upload data (Other data sources also include this option).</li>"\
                    "<li><b>Poll external file system: </b>Setup automatic polling of an external file system from a URL location, when new files of the correct type and naming convention are found they are ingested.<li>"\
                    "<li><b><i>(Advanced)</i> Push to this website through the API:</b>  Use the XMLRPC API to directly push data into persistent storage, on project acceptance you will be emailed your API key and instructions.</li>"\
                    "<li><b>Sensor Observation Service: </b>Set-up a sensor that implements the Sensor Observation Service (SOS) to push data into this systems SOS server.</li>"\
                    "<li><b><i>(Advanced)</i> Output from other dataset: </b>This allows for advanced/chained processing of data, where the results of another dataset can be further processed and stored as required.</li>"\
                    "</ul>",
        placeholder="Select the easiest method for your project.  If all else fails, manual file uploads will work for all data types.")

    name = colander.SchemaNode(colander.String(),
        placeholder="Searchable identifier for this input method (eg. Invertebrate observations)",
        description="Descriptive, human readable name for this input method.  The name will be used to select this method in the <i>Datasets</i> step and will also be searchable within the database.")
    description = colander.SchemaNode(colander.String(), title="Description", widget=deform.widget.TextAreaWidget(),
        description="Provide a description of this method, this should include what, why and how the data is being collected but <b>Don\'t enter where or when</b> as this is information relevant to the dataset, not the method."
        ,
        placeholder="Enter specific details for this method, users of your data will need to know how reliable your data is and how it was collected.")
    url = WebsiteSchema(missing=colander.null, title="Further information (URL)", description="If there are web addresses that can provide more information on your data collection method, add them here.  Examples may include manufacturers of your equipment or an article on the calibration methods used.")
    attachments = Attachments(missing=colander.null, description="Attach information about this method, this is preferred to external URLs as it is persistent.  Example attachments would be sensor datasheets, documentation describing your file/data storage schema or calibration data.")
    custom_fields = CustomFieldsSchema(missing=colander.null, title="Custom Fields", description="Provide details of the schema that this input " \
                                                                         "method requires to store it\'s data along with " \
                                                                         "descriptions for the manual data entry form and " \
                                                                         "further notes to the administrators.")

class DataSchemas(colander.SequenceSchema):
    dataSource = Method(title="Data collection method", collapsed=False, collapse_group="method")

class MethodsSchema(colander.Schema):
    description = colander.SchemaNode(colander.String(), title="Overall methods description",
        widget=deform.widget.TextAreaWidget(rows=5),
        placeholder="Provide an overview of all the data collection methods used in the project and why those methods were chosen.",
        description="Provide a description for all data input methods used in the project.  This will be used as the description for data collection in the project metadata record and will provide users of your data with an overview of what the project is researching.")
    dataSources = DataSchemas(title="Methods", widget=deform.widget.SequenceWidget(min_len=1),
        description="Add 1 method for each type of data collection method (eg. SOS temperature sensors, manually entered field observations using a form or files retrieved by polling a server...)")

