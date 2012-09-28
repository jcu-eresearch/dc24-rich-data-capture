Project DC24: Rich Data Capture - Funded by ANDS
------------------------------------------------
The DC24 project will build software infrastructure to enable the automatic capture and storage of a variety of streaming data and the associated metadata. The data will be stored in a digital asset management system and the metadata will be stored in the JCU Research Data Catalogue.  Harvesters will be setup for Research Data Australia to automatically gather metadata records from JCU’s research data catalogue and publish it nationally.

System Architecture
-------------------
The Daintree Rainforest Observatory project is purchasing a licence to run the [CoastalCOMS]:"http://www.coastalcoms.com/" Digital Asset Manager (CC-DAM) product to store and manage streaming data from the Daintree Rainforest research facilities. As part of the DC24 project, ingesters will be developed to received data from a number of different types of data streams, process these streams as required and feed the data to the CC-DAM from where it can be searched and downloaded via a web-based interface. An ingester platform will be developed and ingesters will be written to accept:
* Video streams
* Acoustic streams
* Sensor data – for a variety of sensor types
* Field observations
* [Sensor Observation Service (SOS)]::"http://www.opengeospatial.org/standards/sos"

Before the ingesters can be used, data feeds will need to be provisioned. A provisioning tool will be developed as part of DC24 that will gather both the technical information required by the CC-DAM as well as the collection level metadata required for the JCU Research Data Catalogue. A researcher will need to complete the provisioning information that the system will then use to configure:
* CC-DAM Ingester instances
* CC-DAM Report and query facilities
* [JCU]:"www.jcu.edu.au" metadata repository (ReDBox)
* Link the metadata record to the CC-DAM data and other records
* [SOS]:"http://www.opengeospatial.org/standards/sos" and Data Turbine

The metadata will be part of the JCU research data catalogue workflow and, when published, will be made available to harvesting by ANDS’ Research Data Australia OAI-PMH harvester.

A [52° North installation of SOS]:"http://52north.org/communities/sensorweb/sos/" will be linked to the CC-DAM and a [Data Turbine]:"http://www.dataturbine.org/" sink will be developed to provide buffering of data if the sensor supports it.

Links
-----
* [TDH-Rich Data Capture Blog]:"http://jcu-eresearch.github.com/TDH-rich-data-capture/"
* [Sensor Observation Service (SOS)]::"http://www.opengeospatial.org/standards/sos"
* [Data Turbine]:"http://www.dataturbine.org/"
* [Australian National Data Service (ANDS)]:"http://www.ands.org.au/"
* [RIF-CS (metadata)]:"http://www.ands.org.au/guides/content-providers-guide.html"
* [Research Data Australia (RDA)]:"http://researchdata.ands.org.au/"