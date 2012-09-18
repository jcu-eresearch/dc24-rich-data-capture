Project DC24: Rich Data Capture

Introduction
------------
This document aims to present the overall system architecture for the DC24 Rich Data Capture project. The DC24 project will build software infrastructure to enable the automatic capture and storage of a variety of streaming data and the associated metadata. The data will be stored in a digital asset management system and the metadata will be stored in the JCU Research Data Catalogue.  Harvesters will be setup for Research Data Australia to automatically gather metadata records from JCU’s research data catalogue and publish it nationally.

System Architecture
-------------------
The Daintree Rainforest Observatory project is purchasing a licence to run the CoastalCOMS Digital Asset Manager (CC-DAM) product to store and manage streaming data from the Daintree Rainforest research facilities. As part of the DC24 project, ingesters will be developed to received data from a number of different types of data streams, process these streams as required and feed the data to the CC-DAM from where it can be searched and downloaded via a web-based interface. An ingester platform will be developed and ingesters will be written to accept:
•	Video streams
•	Acoustic streams
•	Sensor data – for a variety of sensor types
•	Field observations
•	Sensor Observation Service (SOS)
Before the ingesters can be used, data feeds will need to be provisioned. A provisioning tool will be developed as part of DC24 that will gather both the technical information required by the CC-DAM as well as the collection level metadata required for the JCU Research Data Catalogue. A researcher will need to complete the provisioning information that the system will then use to configure:
•	CC-DAM Ingester instances
•	CC-DAM Report and query facilities
•	JCU metadata repository (ReDBox)
•	Link the metadata record to the CC-DAM data and other records
•	SOS and Data Turbine
 The metadata will be part of the JCU research data catalogue workflow and, when published, will be made available to harvesting by ANDS’ Research Data Australia OAI-PMH harvester.
A 52° North installation of SOS will be linked to the CC-DAM and a Data Turbine sink will be developed to provide buffering of data if the sensor supports it.
