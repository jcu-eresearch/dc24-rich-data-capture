from jcudc24provisioning.models import Base
from colanderalchemy.declarative import Column
import deform
from sqlalchemy import (
    Integer,
    Text,
    )
from sqlalchemy.types import BLOB, String


choices = ['JCU Name 1', 'JCU Name 2', 'JCU Name 3', 'JCU Name 4']

class ProjectSchema(Base):
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True, nullable=False, ca_widget=deform.widget.HiddenWidget())

    #--------------Setup--------------------
    project_title = Column(String(), ca_widget=deform.widget.TextInputWidget(css_class="full_width"), ca_page="setup",
                ca_group_start="test", ca_group_description="test description", ca_group_collapsed=False,
                ca_placeholder="An easily identifiable, concise what and why - Include relevant keyword - Keep the description relevant to all generated records.",
                ca_title="Project Title", ca_description="<p>A descriptive title that will make the generated records easy to search and describes the type of data collected and why.</p><p>It is recommended for datasets and collections, the title should be unique to the data, ie. do not use the publication title as the data title.</p><p>Make sure the title contains relevant keywords as it will be searched on and keep the title relevant to all generated records.</p>")

    data_manager = Column(String(), ca_title="Data Manager", ca_page="setup",
        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices),
        ca_placeholder="Autocomplete from JCU's accounts (press the 'Other' tick box for non-JCU)",
        ca_description="Primary contact for the project, this should be the person in charge of the data and actively working on the project.")
    project_lead = Column(String(), ca_title="Project Lead", ca_page="setup",
        ca_widget=deform.widget.AutocompleteInputWidget(min_length=1, values=choices),
        ca_placeholder="Autocomplete from JCU's accounts (press the 'Other' tick box for non-JCU)",
        ca_description="Head supervisor of the project that should be contacted when the data manager is unavailable.")

    #---------------------description---------------------
    brief_description = Column(String(), ca_page="description",
                    ca_placeholder="An executive summary of the full description - Keep the description relevant to all generated records",
                    ca_widget=deform.widget.TextAreaWidget(rows=6), ca_title="Brief Description",
                    ca_description="A short description of the research done, why the research was done and the collection and research methods used.  A short description of the project level where and when can also be included.  Note: Keep the description relevant to all generated records.")
    full_description = Column(String(), ca_widget=deform.widget.TextAreaWidget(rows=20), ca_page="description",
        ca_title="Full Description", ca_placeholder="Full description of the project - Keep the description relevant to all generated records",
        ca_description="<p>Full length description of the research project which will also be used for the metadata records.  This should include:</p>"\
                    "<ul><li>Information about the research dataset/collection, registry/repository, catalogue or index, including its characteristics and features, eg. This dataset contains observational data, calibration files and catalogue information collected from the Mount Stromlo Observatory Facility.</li>"\
                    "<li>If applicable: the scope; details of entities being studied or recorded; methodologies used.</li></ul>")


    #---------------------metadata---------------------