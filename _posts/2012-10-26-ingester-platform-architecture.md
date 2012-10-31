---
layout: post
title: "Ingester Platform Architecture"
description: "What does each part of the ingester platform (currently) do?"
author: "Nigel Sim"
category: 
tags: [overview, andsDataCapture, andsDC24, fundedByAustralianNationalDataService, DIISRTE, andsApps, DC24, richDataCapture]
---
{% include JB/setup %}
	
The ingester platform is a discrete component of the DC24 system that is resposible for collecting, curating, and storing data for the configured projects.

------------	

![High level overview of the ingester platform]({{ site.JB.BASE_PATH }}/images/ingester-platform-arch.png)

Basted on the iteration 1 and 2 requirements the ingester platform has been architected as follows:
1. A scheduler engine to periodically execute the data sampler
2. A sampler that determines if it is time to run a data collector, and then curate the data for ingestion
3. A data collector that interacts with an external system to collect data
4. An ingester queue for storing these collected data in the repository
5. An API to configure, monitor, and retrieve from the ingester platform and repository

By having a separate data queue inside the ingester platform the system is made robust against temperary failyre of the repository. This also allows ingest rates to be controlled in case of large spikes in ingest data.

