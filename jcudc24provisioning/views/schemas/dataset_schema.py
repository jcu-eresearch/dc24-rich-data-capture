import inspect
import colander
import deform
from jcudc24provisioning.views.schemas.common_schemas import Attachment

__author__ = 'Casey Bajema'


class SamplingCondition(colander.MappingSchema):
                                    pass

class SamplingConditionSchema(colander.SequenceSchema):
    todo = colander.SchemaNode(colander.String())

class SamplingSchema(colander.MappingSchema):
    startConditions = SamplingConditionSchema(title="Start conditions", default="todo")
    stopConditions = SamplingConditionSchema(title="Stop conditions")

class CoverageSchema(colander.MappingSchema):
    timePeriodDescription = colander.SchemaNode(colander.String(), title="Time Period (description)", default="A textual description of the time period (eg. Summers of 1996 to 2006)", missing="", description="Provide a textual representation of the time period such as world war 2 or more information on the time within the dates provided.")
    dateFrom = colander.SchemaNode(colander.Date(), default="", title="Date From",
        description='Date data will start being collected.')
    dateTo = colander.SchemaNode(colander.Date(), default="", title="Date To",
        description='Date data will stop being collected.', missing="undefined")
    locationDescription = colander.SchemaNode(colander.String(), title="Location (description)", description="Textual description of the location such as Australian Wet Tropics or further information such as elevation.")
    researchLocation = colander.SchemaNode(colander.String(), title="Research location",
        default="To be redeveloped similar to ReDBox", description="Enter or select the location or region that the project covers.")

class CustomProcessingSchema(colander.MappingSchema):
    customProcessorDesc = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(),
        title="Describe custom processing needs", missing="", description="Describe your processing " \
                    "requirements and what your uploaded script does, or what you will need help with.",
        default="eg. Extract some value from the comma separated file where the value is the first field.")

    customProcessorScript = Attachment(title="Upload custom script", description="Upload a custom Python script to " \
                "process the data in some way.  The processing script API can be found " \
                "<a title=\"Python processing script API\"href=\"\">here</a>.")

class InternalMethodSchema(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.", description="Provide a dataset specific description that will be appended to the project description in metadata records.")
    sampling = SamplingSchema()
    customProcessing = CustomProcessingSchema(title="Custom processing")

class MethodSchema(colander.MappingSchema):
    disableMetadata = colander.SchemaNode(colander.Boolean(), widget=deform.widget.CheckboxWidget(),
        title='Don\'t create metadata record', description="Disable ReDBox metadata record generation.  Only check this if the dataset is an intermediate processing step or the data shouldn\\'t be published for some other reason.")
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.", description="Provide a dataset specific description that will be appended to the project description in metadata records.")
    coverage = CoverageSchema()
    sampling = SamplingSchema(description="Provide filtering conditions for the data received, the most common and simplest" \
                                          "cases are a sampling rate (eg. once per hour) or a repeating time periods (such as " \
                                          "start at 6am, stop at 7am daily) but any filtering can be acheived by adding a custom " \
                                          "sampling script.</br></br>  The sampling script API can be found <a href="">here</a>.")
    # TODO: Finish the sampling schema
    customProcessing = CustomProcessingSchema(title="Custom processing")

class DataSourceSchemas():
    class PushDataSourceSchema(colander.MappingSchema):
        class PushDataSourceSchema(colander.MappingSchema):
            key = colander.SchemaNode(colander.String(), "A unique API key that can be used for authentication.", readonly=True)

        class PullDataSourceSchema(colander.MappingSchema):
            url = colander.SchemaNode(colander.String(), "Location of the server to poll.")

        class SOSDataSourceSchema(colander.MappingSchema):
            serverURL = colander.SchemaNode(colander.String(), "Location of the SOS server.")
            sensorID = colander.SchemaNode(colander.String(), "ID of the SOS sensor.")

class MethodSelectSchema(colander.MappingSchema):
    method = MethodSchema()
    internal = InternalMethodSchema()

    def __init__(self):
        pass
#        for all methods:
#            method = MethodSchema()
#            for name, obj in inspect.getmembers(foo):
#                if inspect.isclass(obj):
#                    method.add(api2colander(dataSourceSchema))
#            self.add(method)
#        self.add(InternalMethodSchema())

class Dataset(colander.SequenceSchema):
    dataSource = MethodSelectSchema(title="Method", widget=deform.widget.MappingWidget(template="select_mapping"), description="Select the data collection method for this dataset, the methods need to have been setup in the previous workflow step.")

class DatasetSchema(colander.MappingSchema):
    dataInputs = Dataset(title="Datasets", widget=deform.widget.SequenceWidget(min_len=1))