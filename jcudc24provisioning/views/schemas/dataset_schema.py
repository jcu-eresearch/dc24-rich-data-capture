import colander
import deform
from jcudc24provisioning.views.workflow.workflows import MemoryTmpStore

__author__ = 'Casey Bajema'


class SamplingCondition(colander.MappingSchema):
    todo = colander.SchemaNode(colander.String(), default="TO BE DEVELOPED")

class SamplingConditionSchema(colander.SequenceSchema):
    condition = SamplingCondition()

class SamplingSchema(colander.MappingSchema):
    startConditions = SamplingConditionSchema(title="Start conditions")
    stopConditions = SamplingConditionSchema(title="Stop conditions")

class CoverageSchema(colander.MappingSchema):
    timePeriodDescription = colander.SchemaNode(colander.String(), title="Time Period (description)", default="A textual description of the time period (eg. Summers of 1996 to 2006)", missing="", description="Provide a textual representation of the time period such as world war 2 or more information on the time within the dates provided.")
    dateFrom = colander.SchemaNode(colander.Date(), default="", title="Date From",
        description='Date data will start being collected.')
    dateTo = colander.SchemaNode(colander.Date(), default="", title="Date To",
        description='Date data will stop being collected.')
    locationDescription = colander.SchemaNode(colander.String(), title="Location (description)", description="Textual description of the location such as Australian Wet Tropics or further information such as elevation.")
    researchLocation = colander.SchemaNode(colander.String(), title="Research location",
        default="To be redeveloped similar to ReDBox", description="Enter or select the location that the data will be collected at.")

class CustomProcessingSchema(colander.MappingSchema):
    customProcessorDesc = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(),
        title="Describe custom processing needs", missing="", description="Describe your processing " \
                    "requirements and what your uploaded script does, or what you will need help with.")

    script = MemoryTmpStore()
    customProcessorScript = colander.SchemaNode(colander.String(),
        #*deform.FileData(), widget=deform.widget.FileUploadWidget(script),*#
        title="Upload custom script", default="Upload widget isn't working yet...", description="Upload a custom" \
                "Python script to process the data in some way.  The processing script API can be found " \
                "<a title=\"Python processing script API\"href=\"\">here</a>.")

class ManualEntrySchema(colander.MappingSchema):
    disableMetadata = colander.SchemaNode(colander.Boolean(), widget=deform.widget.CheckboxWidget(),
        title='Don\'t create metadata record', description="Disable ReDBox metadata record generation.  Only check this if the dataset is an intermediate processing step or the data shouldn\\'t be published for some other reason.")
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.", description="Provide a dataset specific description that will be appended to the project description in metadata records.")
    coverage = CoverageSchema()
    customProcessing = CustomProcessingSchema(title="Custom processing")

class VideoSchema(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.")
    coverage = CoverageSchema()
    videoURL = colander.SchemaNode(colander.String(), title="Audio\Video URL")
    samplingConditions = SamplingSchema(title="Sampling conditions", description="Configure when the data should be sampled.")
    customProcessing = CustomProcessingSchema(title="Custom processing")

class AudioSchema(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.")
    coverage = CoverageSchema()
    videoURL = colander.SchemaNode(colander.String(), title="Audio\Video URL")
    samplingConditions = SamplingSchema(title="Sampling conditions",description="Configure when the data should be sampled.")
    customProcessing = CustomProcessingSchema(title="Custom processing")

class FileSchema(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.")
    coverage = CoverageSchema()
    customProcessing = CustomProcessingSchema(title="Custom processing")

class SensorSchema(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.")
    coverage = CoverageSchema()
    sosID = colander.SchemaNode(colander.String(), title="Sensor ID (SOS)", default="Linked to SOS/DB")
    customProcessing = CustomProcessingSchema(title="Custom processing")

class MethodSelectSchema(colander.MappingSchema):
    manual = ManualEntrySchema(title="Manual Entry", name="form")
    video = VideoSchema(title="Video Stream", name="video")
    audio = AudioSchema(title="Audio Stream", name="audio")
    file = FileSchema(title="File Upload", name="file")
    sensor = SensorSchema(title="Sensor Stream", name="sensor")

class Dataset(colander.SequenceSchema):
    dataSource = MethodSelectSchema(title="Method", widget=deform.widget.MappingWidget(template="select_mapping"), description="Select the data collection method for this dataset, the methods need to have been setup in the previous workflow step.")

class DatasetSchema(colander.MappingSchema):
    dataInputs = Dataset(title="Datasets", widget=deform.widget.SequenceWidget(min_len=1))