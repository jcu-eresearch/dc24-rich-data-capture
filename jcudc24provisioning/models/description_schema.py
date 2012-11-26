import colander

__author__ = 'Casey'

from sqlalchemy.types import String, Integer
from colanderalchemy.declarative import Column
import deform

__author__ = 'Casey Bajema'

class DescriptionSchema(colander.MappingSchema):
    brief_description = Column(String(),
                ca_placeholder="An executive summary of the full description - Keep the description relevant to all generated records",ca_page="description",
                ca_widget=deform.widget.TextAreaWidget(rows=6), ca_title="Brief Description",
                ca_description="A short description of the research done, why the research was done and the collection and research methods used.  A short description of the project level where and when can also be included.  Note: Keep the description relevant to all generated records.")
    full_description = Column(String(), ca_widget=deform.widget.TextAreaWidget(rows=20), ca_page="description",
        ca_title="Full Description", ca_placeholder="Full description of the project - Keep the description relevant to all generated records",
        ca_description="<p>Full length description of the research project which will also be used for the metadata records.  This should include:</p>"\
                    "<ul><li>Information about the research dataset/collection, registry/repository, catalogue or index, including its characteristics and features, eg. This dataset contains observational data, calibration files and catalogue information collected from the Mount Stromlo Observatory Facility.</li>"\
                    "<li>If applicable: the scope; details of entities being studied or recorded; methodologies used.</li></ul>")
