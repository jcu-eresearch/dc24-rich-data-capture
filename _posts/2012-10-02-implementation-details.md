---
layout: post
title: "Updated Implementation Details"
description: "Provides an overview of the current architectures and implementation details of the TDH-DC24 Rich Data Capture project."
author: casey
category: technology
tags: [andsTechnology, andsArchitecture, DIISRTE, fundedByAustralianNationalDataService, andsApps, DC24, richDataCapture, RDC]
---
{% include JB/setup %}

Over the last month development effort has been spent on firming up the architecture being used, finding the best provisioning workflows and initial implementation of the provisioning interface. 

Provisioning Interface
----------------------
The technologies chosen for the provisioning interface itself are [Python (2.7)](http://www.python.org/) using the [Pyramid](http://docs.pylonsproject.org/en/latest/docs/pyramid.html) and [Deform](http://docs.pylonsproject.org/projects/deform/en/latest/?awesome) frameworks.  These technologies were chosen primarily because:
- [Python](http://www.python.org/) is a high performance and highly productive scripting language as well as the preferred language of the long term maintenance and support staff.
- [Pyramid](http://docs.pylonsproject.org/en/latest/docs/pyramid.html) provides a reliable, easy to use and flexible templating system.
- [Deform](http://docs.pylonsproject.org/projects/deform/en/latest/?awesome) is a schema based form framework that can be used for quick development and dynamic form generation.



###Workflow

</br>

![Provisioning workflow]({{ site.JB.BASE_PATH }}/images/workflow.png)

_Orange is general setup and control steps, green is plain metadata collection and blue is used to prepare the CC-DAM to receive data._

</br>

|Workflow Step | Purpose | 
|--- | ---
|General| Collects project descriptions and contact details used for setting up a project|
|Metadata| Collects all relevant metadata such as required by [RIF-CS](www.ands.org.au/training/rif-cs/index.html) and [JCU](www.jcu.edu.au) |
|Methods| Setup data collection methods that the project will use (eg. a temperature sensor that will provide data as manually uploaded files. And the datasheets and calibration iformation would be attached to the method).|
|Datasets| Setup datasets that the project will collect, this is really a data collection method at a set location and per-dataset provisioning requirements (eg. sensor id for [SOS](http://www.opengeospatial.org/standards/sos) data collection methods) |
|Submit| Submit or delete the project.  Once the project is submitted and approved there may be limitations on what can be edited. |

</br>

The data provisioning has been split into methods and datasets to:
- Reuse as much data as possible, for example a current project uses the same observation forms for 25+ sites throughout north Queensland, by breaking it into two steps the form only needs to be set-up once and each site is entered as a dataset using that form method.
- Try and logically seperate the data into two simpler forms.

Methods (ingesters) that will be set-up as part of the Rich Data Capture (RDC) project include:
- Web forms (Field Obs)
- File upload (Sensors where the data is manually uploaded)
- Push or pull file streaming (Video and audio)
- [SOS](http://www.opengeospatial.org/standards/sos)

The main difference between the above methods and the original five ingesters is that generic terminology has been used.

[ReDBox](http://www.redboxresearchdata.com.au/) metadata will be compiled from the information entered in all steps which means that a large project that has multiple datasets will only require the large portion of repeated metadata to be entered once. 



CoastalCOMS Data Access Management (CC-DAM)
-------------------------------------------
The CC-DAM is the persistent data storage being used and is based on flat file storage using a relational database to hold management and indexing data.  This provides an efficient and scalable storage architecture but has some implications:
- Efficient searching within the CC-DAM requires the ingester to index relevent fields in advance.
- Data storage is flat rather than a relational database that has links between tables that can be searched across.

CoastalCOMS is providing an ingestor platform that will be written in [Python (2.7)](http://www.python.org/) and will provide API's for:
- Adding or retreiving data input methods which sets up ways of entering data into the CC-DAM.
- Adding or retreiving datasets, which sets up an instance of a data input method to be used by a project and contains collection metadata such as location.
- Adding or retreiving data entries which are the actual data points and will be linked to a dataset.

This structure has been chosen to integrate with the workflow and provide a framework for adding future projects and data input methods.  

[Sensor Observation Service (SOS)](http://www.opengeospatial.org/standards/sos)
--------------------------------
After further investigation the SOS won't be implemented by developing a data layer for the [52&#176; North](http://52north.org/) implementation for the following reasons:
- The [52&#176; North](http://52north.org/) implementation is structured around a relational database that doesn't fit with the CC-DAM and flat file storage.
- The data layer is a lot more complicated than is required for this project and will require unnecessary development time.  
- The primary purpose of the CC-DAM and the Rich Data Capture project is reliable, efficient data storage rather than implementing application specific programs.

The [SOS](http://www.opengeospatial.org/standards/sos) implementation isn't finalised at this point but we are looking at the following 2 options:
1. Implement a minimal [SOS](http://www.opengeospatial.org/standards/sos) service that stores the [SensorML](http://www.ogcnetwork.net/SensorML) and [Observation & Measurement](http://www.opengeospatial.org/standards/om) XML files directly in the CC-DAM.
2. Use an extrnal [SOS](http://www.opengeospatial.org/standards/sos) (such as the [52&#176; North](http://52north.org/) implementation) and the provisioning interface polls it regularly for the [SensorML](http://www.ogcnetwork.net/SensorML) and [Observation & Measurement](http://www.opengeospatial.org/standards/om) XML files which are then stored permanently in the CC-DAM.

Further processing or full [SOS](http://www.opengeospatial.org/standards/sos) features could be accessed by exporting the [SensorML](http://www.ogcnetwork.net/SensorML) and [Observation & Measurement](http://www.opengeospatial.org/standards/om) XML to an external [SOS](http://www.opengeospatial.org/standards/sos) implementation.
