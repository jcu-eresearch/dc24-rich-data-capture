import colander
import deform
from views.workflow.workflows import MemoryTmpStore

__author__ = 'Casey Bajema'


class SamplingCondition(colander.MappingSchema):
    todo = colander.SchemaNode(colander.String(), default="TO BE DEVELOPED")

class SamplingConditionSchema(colander.SequenceSchema):
    condition = SamplingCondition()

class SamplingSchema(colander.MappingSchema):
    startConditions = SamplingConditionSchema(title="Start conditions")
    stopConditions = SamplingConditionSchema(title="Stop conditions")

class CoverageSchema(colander.MappingSchema):
    timePeriodDescription = colander.SchemaNode(colander.String(), title="Time Period (description)", default="A textual description of the time period (eg. Summers of 1996 to 2006)")
    dateFrom = colander.SchemaNode(colander.Date(), default="", title="Date From",
        description='Date data will start being collected')
    dateTo = colander.SchemaNode(colander.Date(), default="", title="Date To",
        description='Date data will stop being collected')
    locationDescription = colander.SchemaNode(colander.String(), title="Location (description)")
    researchLocation = colander.SchemaNode(colander.String(), title="Research location",
        default="To be redeveloped similar to ReDBox")

class CustomProcessingSchema(colander.MappingSchema):
    customProcessor = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(),
        title="Describe custom processing needs", missing="")

    script = MemoryTmpStore()
    customProcessorScript = colander.SchemaNode(colander.String(),
        #*deform.FileData(), widget=deform.widget.FileUploadWidget(script),*#
        title="Upload custom script", default="Upload widget isn't working yet...")

class ManualEntrySchema(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.")
    coverage = CoverageSchema()
    customProcessing = CustomProcessingSchema(title="Custom processing")

class VideoSchema(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.")
    coverage = CoverageSchema()
    videoURL = colander.SchemaNode(colander.String(), title="Audio\Video URL")
    samplingConditions = SamplingSchema(title="Sampling conditions")
    customProcessing = CustomProcessingSchema(title="Custom processing")

class AudioSchema(colander.MappingSchema):
    description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(), default="Provide a textual description of the dataset being collected.")
    coverage = CoverageSchema()
    videoURL = colander.SchemaNode(colander.String(), title="Audio\Video URL")
    samplingConditions = SamplingSchema(title="Sampling conditions")
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
    manual = ManualEntrySchema(title="Manual Entry", name="form", description="test")
    video = VideoSchema(title="Video Stream", name="video")
    audio = AudioSchema(title="Audio Stream", name="audio")
    file = FileSchema(title="File Upload", name="file")
    sensor = SensorSchema(title="Sensor Stream", name="sensor")

