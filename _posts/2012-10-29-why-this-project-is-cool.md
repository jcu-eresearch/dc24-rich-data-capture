---
layout: post
title: "Why this project is cool"
description: "What is cool about this project, why would the wider community care about it and what is the overall ecosystem that this project is part of."
author: "Casey Bajema"
category: 
tags: [overview, andsDataCapture, andsDC24, fundedByAustralianNationalDataService, DIISRTE, andsApps, DC24, richDataCapture]
---
{% include JB/setup %}
	
The primary purpose of this project is increased ease-of-use and speed for researchers to enter data and associated metadata into persistant storage.

------------	
<p style="font-size: 1.1em;"><b>Research data.</b><br /></p>

<p><i>Sounds kinda boring right?</i><br /></p>
<p><i>Why should you care?</i></p>
<p>Think of research data as information scientists &amp; engineers have available for creating new technologies such as mapping how climate change will effect your life in the next 30 years, the latest medical cures or preserving our great Australian environment - almost anything you can think of, the building blocks of our entire modern lifestyle is research&#33;</p>

	Can you see how research data effects your everyday life in real ways?

Research is obviously not new but their have been great strides in making it easier to share and re-use research data nationally throughout Australia, and this project is a tool that takes it one step further:
* Automatic data collection from supported sensors in the field.
* Semi-automatic generation of metadata (information describing the data). 
* An easy web interface to encourage researchers to add their data and share it nationally.

![High level overview diagram illustrating the interacting systems and how this project fits in.]({{ site.JB.BASE_PATH }}/images/high_level_overview.png)
*Figure 1.  High level overview of the systems involved and how the Rich Data Capture project fits into it.*

<br />
**Why is this project cool?**  
Because it will increase the effeciency of creating and sharing research data, which means quicker progress within Australia as a whole, higher potential for new technologies and a better understanding of our environment.

<br />

### External Systems

**[Australian National Data Service (ANDS)](http://ands.org.au/)** is an organisation focused on making research data from numerous sources throughout australia publicly available along with information that describes the data so that other researchers can easily re-use it and know that the data is good quality.

**[ReDBox and Mint](http://www.redboxresearchdata.com.au/)** are metadata repositories that provide metadata feeds to ANDS and therefore publishing the research accross Australia.

**[CoastalCOMS Data Access Management (CC-DAM)](http://www.coastalcoms.com/)** provides persistant storage for the actual data.  CC-DAM will be accessed using the open source API that is being developed as part of this project.