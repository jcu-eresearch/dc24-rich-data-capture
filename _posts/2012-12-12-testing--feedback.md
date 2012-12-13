---
layout: post
title: "Testing &#38; Feedback"
description: "Outline of the development, testing and feedback process used throughout this project."
author: "casey"
category: 
tags: [testing, feedback, DIISRTE, fundedByAustralianNationalDataService, andsApps, DC24, richDataCapture]
---
{% include JB/setup %}

Initially the DC24-Rich Data Capture projects specifications were loosely defined (all projects that aim to build a generic framework for the future are always difficult to define!) so an agile development process has been used with an emphasis on continual testing and feedback of the project requirements and deliverables.  

The process can be described in the following steps:
* Initial requirements gathering
* Further investigation and scoping
* Development with regular end user demonstrations and feedback 

Initial Requirements Gathering
------------------------------

With the project description as a starting point the following sources were researched/interviewed and analysed to find research requirements and used to scope out commonalities that could be built into as generic a framework as possible:
* [Daintry Rainforest Observatory](http://www.jcu.edu.au/canopycrane/index.htm) Australian Wet Tropics (Broad range of environmental monitoring - non-networked sensors and manual observations)
* [Daintry Rainforest Observatory](http://www.jcu.edu.au/canopycrane/index.htm) Artificial tree (Rainforest temperature and humidity sensors - networked)
* [Bush-FM](http://www.bush.fm/) (Acoustic recordings - non-networked sensors)
* [SEMAT](http://eresearch.jcu.edu.au/projects/semat) (Marine sensor bouys - networked)
* [CoastalCOMS](http://www.coastalcoms.com/) (commercial experience with networked video ingestion)
* Heads of [JCU eResearch](http://eresearch.jcu.edu.au/) (Research and IT experience)

The first five blog posts were put together during the initial requirements gathering process.

Further Investigation & Scoping
-------------------------------

After the initial requirements gathering process the three core focuses were:
* Preparing the underlying frameworks such as [CoastalCOMS](http://www.coastalcoms.com/) Data Access Management.
* Defining the ingetser platform API - how the provisioning interface (website) communicates with the ingester platform (framework for persistent storage).
* Developing (non-functional) workflow forms for the purpose of demonstrationing the solution and an indepth investigation of the full requirements. 

During this phase we firmed up the scope documentation and presented it to the end users and parties involved along with the initial development done, the resulting scope was outlined in the Updated Implementation Details and Ingester Platform Architecture blogs. 

Development, Testing & Feedback  
-------------------------------

Development bagan in earnest in this phase with regular demonstrations and feedback at roughly fortnightly intervals from:
* Projects and parties stated above
* Other developers specialised in user interface design
* Additional researchers (the target end user) have been approached to provide testing in the near future

An example demonstration and feedback session last fortnight involved:
* [Nigel Sim]({{ site.JB.BASE_PATH }}/2012/08/27/the-team/#nigel_s) screen sharing the process of ingesting a file using the ingester platform
* [Casey Bajema]({{ site.JB.BASE_PATH }}/2012/08/27/the-team/#casey) demonstrated the steps involved in the provisioning workflow, describing the process of setting up automated ingestion of data along with its schemas/indexing and metadata.  Initial forms also showed the functionality of project actions after the project is setup (eg. quality assurance, manual data input and getting data out of the system).
* Presented to Ian Atkinson, Jeremy Vanderwal and [Marianne Brown]({{ site.JB.BASE_PATH }}/2012/08/27/the-team/#marianne)

At the time of writing the provisioning interface and ingester platform are in the early stages of functionality and feedback will start to progress from theoretical/demonstrations into actual use in the coming weeks allowing for more hands-on end user testing.  

A virtual machine ([damrdc.hpc.jcu.edu.au](http://damrdc.hpc.jcu.edu.au) - requires [JCU](http://www.jcu.edu.au/) network access) has been setup allowing access to the current stable version at any time encouraging as much feedback as possible. 
