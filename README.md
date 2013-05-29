# EnMaSSe Provisioning Interface

There have been great strides in making it easier to share and re-use research data throughout Australia, and EnMaSSe is a tool that takes it one step further.  EnMaSSe is designed to increase the efficiency of creating and sharing research data, which means quicker progress within Australia as a whole, higher potential for new technologies and a better understanding of our environment.

Think of research data as information scientists & engineers have available for creating new technologies such as mapping how climate change will affect your life in the next 30 years, the latest medical cures or preserving our great Australian environment - almost anything you can think of, the building blocks of our entire modern lifestyle is research!

The EnMaSSe application provides a user-friendly interface for:

* Flexible and scalable research data ingestion (both streamed or manually input).
* High quality, fine grained, project based, metadata creation and export (eg. Enter 1 record, export many).
* Administerable and maintainable project lifecycle and workflows.

This project has been developed as part of EnMaSSe (Environmental Monitoring and Sensor Storage) and is related to:

* [Documentation](https://github.com/jcu-eresearch/TDH-Rich-Data-Capture-Documentation) - Contains full user, administrator and developer guides.
* [Deployment](https://github.com/jcu-eresearch/EnMaSSe-Deployment) - Recommended way to install
* [Ingester Platform](https://github.com/jcu-eresearch/TDH-dc24-ingester-platform) - Handles ingestion of data streaming and storage for the EnMaSSe project.
* [Ingester API](https://github.com/jcu-eresearch/jcu.dc24.ingesterapi) - API for integrating the EnMaSSe provisioning interface with the ingester platform (this)
* [SimpleSOS](https://github.com/jcu-eresearch/python-simplesos) - Library used for the SOSScraperDataSource.
 

# Installation

**Please refer to the [Deployment](https://github.com/jcu-eresearch/EnMaSSe-Deployment) repository for installation instructions.**

Links
-----
* [User Guide]:"https://tdh-rich-data-capture-documentation.readthedocs.org/en/latest/enmasse-user.html"
* [Administrator Guide]:"https://tdh-rich-data-capture-documentation.readthedocs.org/en/latest/enmasse-admin.html"
* [Developer Dcumentation]:"https://tdh-rich-data-capture-documentation.readthedocs.org/en/latest/enmasse-developer.html"
* [TDH-Rich Data Capture Blog]:"http://jcu-eresearch.github.com/TDH-rich-data-capture/"
* [Sensor Observation Service (SOS)]::"http://www.opengeospatial.org/standards/sos"
* [Australian National Data Service (ANDS)]:"http://www.ands.org.au/"
* [RIF-CS (metadata)]:"http://www.ands.org.au/guides/content-providers-guide.html"
* [Research Data Australia (RDA)]:"http://researchdata.ands.org.au/"


Credits
-------

This project is supported by [the Australian National Data Service (ANDS)](http://www.ands.org.au/) through the National Collaborative Research Infrastructure Strategy Program and the Education Investment Fund (EIF) Super Science Initiative, as well as through the [Queensland Cyber Infrastructure Foundation (QCIF)](http://www.qcif.edu.au/).

License
-------

See `LICENCE.txt`.
