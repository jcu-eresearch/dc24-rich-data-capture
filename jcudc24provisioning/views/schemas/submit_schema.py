import colander
import deform

__author__ = 'Casey Bajema'

class CommentsSchema(colander.SequenceSchema):
    comment = colander.SchemaNode(colander.String(), help="Descriptive help text test",
        placeholder="eg. Please enter all metadata, the supplied processing script has errors, please extend the existing temperature data type so that your data is searchable, etc..."
        , widget=deform.widget.TextAreaWidget(rows=3))


class submit_schema(colander.MappingSchema):
    comments = CommentsSchema(description="Project comments that are only relevant to the provisioning system (eg. comments as to why the project was reopened after the creator submitted it).")

