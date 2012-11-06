import colander
import deform

__author__ = 'Casey Bajema'

class setup_schema(colander.MappingSchema):
    project_title = colander.SchemaNode(colander.String(), widget=deform.widget.TextInputWidget(css_class="full_width"),
        default="An easily identifiable, concise what and why - Include relevant keyword - Keep the description relevant to all generated records.", title="Project Title",
        description="<p>A descriptive title that will make the generated records easy to search and describes the type of data collected and why.</p><p>It is recommended for datasets and collections, the title should be unique to the data, ie. do not use the publication title as the data title.</p><p>Make sure the title contains relevant keywords as it will be searched on and keep the title relevant to all generated records.</p>")

    brief_description = colander.SchemaNode(colander.String(), help="Descriptive help text test",
        default="An executive summary of the full description - Keep the description relevant to all generated records", widget=deform.widget.TextAreaWidget(rows=3),
        title="Brief Description",
        description="A short description of the research done, why the research was done and the collection and research methods used.  A short description of the project level where and when can also be included.  Note: Keep the description relevant to all generated records.")
    full_description = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget(rows=6),
        title="Full Description", default="Full description of the project - Keep the description relevant to all generated records",
        description="<p>Full length description of the research project which will also be used for the metadata records.  This should include:</p>"\
                    "<ul><li>Information about the research dataset/collection, registry/repository, catalogue or index, including its characteristics and features, eg. This dataset contains observational data, calibration files and catalogue information collected from the Mount Stromlo Observatory Facility.</li>"\
                    "<li>If applicable: the scope; details of entities being studied or recorded; methodologies used.</li></ul>")
    #    TODO: Link to JCU authentication and user lists
    choices = ['JCU Name 1', 'JCU Name 2', 'JCU Name 3', 'JCU Name 4']
    data_manager = colander.SchemaNode(colander.String(), title="Data Manager",
        widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices),
        default="Autocomplete from JCU's accounts (press the 'Other' tick box for non-JCU)",
        description="Primary contact for the project, this should be the person in charge of the data and actively working on the project.")
    project_lead = colander.SchemaNode(colander.String(), title="Project Lead",
        widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices),
        default="Autocomplete from JCU's accounts (press the 'Other' tick box for non-JCU)",
        description="Head supervisor of the project that should be contacted when the data manager is unavailable.")
