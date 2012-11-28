from sqlalchemy.types import String
from colanderalchemy.declarative import Column
import deform

__author__ = 'Casey Bajema'

#choices = ['JCU Name 1', 'JCU Name 2', 'JCU Name 3', 'JCU Name 4']
class SetupSchema():
    project_title = Column(String(), ca_widget=deform.widget.TextInputWidget(css_class="full_width"), ca_page="setup",
            ca_group_start="test", ca_group_description="test description", ca_group_collapsed=False,
            ca_placeholder="An easily identifiable, concise what and why - Include relevant keyword - Keep the description relevant to all generated records.",
            ca_title="Project Title", ca_description="<p>A descriptive title that will make the generated records easy to search and describes the type of data collected and why.</p><p>It is recommended for datasets and collections, the title should be unique to the data, ie. do not use the publication title as the data title.</p><p>Make sure the title contains relevant keywords as it will be searched on and keep the title relevant to all generated records.</p>")

#    data_manager = Column(String(), ca_title="Data Manager", ca_page="setup",
#        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices),
#        ca_placeholder="Autocomplete from JCU's accounts (press the 'Other' tick box for non-JCU)",
#        ca_description="Primary contact for the project, this should be the person in charge of the data and actively working on the project.")
#    project_lead = Column(String(), ca_title="Project Lead", ca_page="setup",
#        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices),
#        ca_placeholder="Autocomplete from JCU's accounts (press the 'Other' tick box for non-JCU)",
#        ca_description="Head supervisor of the project that should be contacted when the data manager is unavailable.")

