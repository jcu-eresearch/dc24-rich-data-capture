---
layout: post
title: "Key Technologies &#38; Key features"
description: "This project will develop a provisioning tool for CoastalCOMS Data Access Management (CC-DAM) and ReDBox-Mint providing a single interface for researchers to enter their data and metadata."
author: "casey"
category: 
tags: [andsFeatures, andsFunctions, andsTechnology, andsArchitecture, andsTools, DIISRTE, fundedByAustralianNationalDataService, andsApps, DC24, richDataCapture]
---
{% include JB/setup %}

Major Features
--------------
There are technologies available for storing data and metadata as well as providing processing, publishing and searching services.  The core feature of this project is to tie those technologies together and provide the end users with a single, intuitive interface to interact with it.

It is critical to make configuring a datasets metadata, ingesters, processors and reports as intuitive as possible while requiring [RIF-CS](http://www.ands.org.au/guides/content-providers-guide.html) compliant metadata.

Types of research data that the system will initially be configured for:
<ul>
	<li>Video</li>
	<li>Acoustic</li>
	<li>Sensor data - for a variety of sensor types</li>
	<li>Field observations</li>
</ul>

Architecture
------------
<img class="diagram" src="{{ site.JB.BASE_PATH }}/images/high-level-architecture.png">

Technology
----------
The provisioning interface will be delivered in browser closely linked to the [ReDBox](http://www.redboxresearchdata.com.au/) system and will provide a user friendly workflow for entering all configuration and metadata about the project at a single location.  The entered data will be passed to the [CoastalCOMS](http://www.coastalcoms.com/) Data Access Management (CC-DAM), [Sensor Observation Service (SOS)](http://www.opengeospatial.org/standards/sos) and [ReDBox-Mint](http://www.redboxresearchdata.com.au/) systems to tie them together as a single easy to use system.

The implementation of [SOS](http://www.opengeospatial.org/standards/sos) provided by [52&#176; North](http://52north.org/) will be used to receive environmental sensor data and metadata from the devices themselves.  A new data layer will need to be written based on the CC-DAM system.  A [Data Turbine](http://www.dataturbine.org/) sink implementation will written to allow buffering of data sent to the [SOS](http://www.opengeospatial.org/standards/sos), it will be optional to use the [Data Turbine](http://www.dataturbine.org/).

CC-DAM will be used for data ingestion and storage.  CC-DAM is proprietary software that will be setup and configured at [James Cook University](http://www.jcu.edu.au/) with an open source ingester platform developed in [Java](http://www.java.com/en/) with a [JSON](http://www.json.org/) API and ingesters will be written in [Python](http://www.python.org/).

[JCU's](http://www.jcu.edu.au) [ReDBox-Mint](http://www.redboxresearchdata.com.au/) installation will be used for storing, searching and publishing research metadata.  ReDBox captures collection metadata (information about research data) whereas Mint is a name authority and vocabulary system (information about people, activities and services).  Both ReDBox and Mint provide an [OAI-PMH](http://www.openarchives.org/pmh/) interface for harvesting their information and will be configured for [Research Data Australia (RDA)](http://researchdata.ands.org.au/) so that metadata is published nationally.

Development Effort
------------------
One major area of development effort is making the interface as easy to use as possible so that researchers readily use the system and provide as much information as possible.  This includes well developed form elements, a good workflow and ease of configuring/adding new storage schemas or processes.

The second major area of development effort will be ensuring metadata is as complete as possible, this is essential for providing data that is easy to reuse, which is the core principle of this project.  This will be implemented by requiring the minimum [RIF-CS](http://www.ands.org.au/guides/content-providers-guide.html) metadata before the configuration is valid and developing the interface to encourage the user to add other relevant metadata.

The third major area of development effort will be creating ingesters and storage schema configurations that are as adaptable as possible so that most project can be setup without requiring custom coding.


The Source
----------
The project uses a local install of Redmine for project tracking, Jenkins for integration testing, and hosts the source at a github repository.

The source is available under the [three-clause BSD licence](http://localhost:8080/metadata).

