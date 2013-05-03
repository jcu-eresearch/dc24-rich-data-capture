---
layout: post
title: "Case Study: Artificial Tree Setup (Part 2)"
description: ""
author: ""
category: 
tags: []
---
{% include JB/setup %}

<style>
	.workflow_image a {
		color: rgb(0, 136, 204);
		font-style: italic;
	}

	.workflow_image img {
		box-shadow: 0 0 6px black;
		padding: 0px;	
		margin: 10px 0px;
		background: white;
		border-radius: 7.5px;
		border: 0px solid transparent;
	}
	
	/*.workflow_image a:hover + img  {	
		display: block;
		width: auto;
		position: absolute;
		z-index: 9999;
		top: 10px;
	}*/	
	
	#lightbox {
		display: none;
		width: auto;
		position: absolute;
		z-index: 9999;
		top: 25px;
		left: 50%;
		background: none;
	}
	
	#lightbox img {
		overflow: hidden;
		box-shadow: 0 0 6px black;
		padding: 0px;
		margin: 10px;
		border-radius: 7.5px;
		border: 0px solid transparent;
	}
	
	#lightbox a {
		padding: 2px 6px;
		border-radius: 25px;
		border: 1px solid rgba(247, 147, 30, 1);
		background: white;
		display: block;
		position: absolute;
		top: -8px;
		right: -5px;
		font-weight: bold;
		color: red;
	}
	#lightbox a:hover {
		text-decoration: none;
		color: black;
	}
	
</style>
<script type="text/javascript">
	function enlarge(img_id) {	
		var lightbox = document.getElementById("lightbox");
		if (lightbox.style.display == "none" || lightbox.last != img_id) {
			lightbox.last = img_id
			lightbox.style.display="block";	
			var lightbox_content = document.getElementById("lightbox_content");
			lightbox_content.innerHTML = document.getElementById(img_id).innerHTML;
			
			lightbox.style.marginLeft = "-" + lightbox.offsetWidth/2 +"px";	
			lightbox.style.top = document.documentElement.scrollTop + 25 +"px";			
		} else {
			lightbox.style.display="none";	
		}
		
	}
</script>

<span id="lightbox">
	<span id="lightbox_content">asdf</span>
	<a onclick="document.getElementById('lightbox').style.display='none'">X</a>
</span>

<br />
#<b style="color: red;">Pictures need updating with relevent metadata included!</b>
<br />

It is recommended that you read [Artificial Tree Overview (Part 1)]({{ site.JB.BASE_PATH }}/2013/01/31/case-study-artificial-tree-overview-part-1) first, which gives an overview of the provisioning interface and the artificial tree.

Artificial Sensor Tree Configuration
====================================

Part 2 walks through each step of the EnMaSSe project creation workflow and explains what needs to be setup.

This project will consist of two data collection methods (an artificial tree and an artificial tree sensor) and two datasets:
* Artificial tree dataset ingests the raw aggregated data from the artificial tree, this consists of all temperature and humidity readings of 10-40 pairs of sensors written to a file every hour.
* Artificial tree sensor dataset processes the raw data and ingests just the temperature and humidity readings of the one specified sensor.
* For a real project, each sensor pair on the artificial tree would have an associated dataset.

###1. Project Creation

The first step is to create a new project (click the New Project item in the main menu), this consists of a creation wizard that pre-fills fields based on the selected project template and the associated research grant as well as collecting the primary contacts.

Project templates allow for pre-filling of any/all fields, and provides the maximum time-savings when there are projects that are similar - equivalent functionality can be acheived using duplicate project in the sidebar (which isn't shown). 

<i>Collected data is for metadata records.</i>

<span class="workflow_image" id="create_page"><img src="{{ site.JB.BASE_PATH }}/images/new_project.png" /></span>
Figure 1: Screenshot of project creation page (Project templates are hidden by default) <a onclick="enlarge('create_page');">[Enlarge]</a>.


###2. General Details

After project creation the general details page is displayed and collects metadata including the title, associated grant and information about all associated people, groups and organisations.

If a research grant was provided in the project creation step:
* Project title is pre-filled with the grant title as a starting point
* Any additional people associated with the research grant are added to the people section.

<i>Collected data is for metadata records.</i>

<span class="workflow_image" id="details_page"><img src="{{ site.JB.BASE_PATH }}/images/general_details.png" /></span>
Figure 2: Screenshot of general details page <a onclick="enlarge('details_page');">[Enlarge]</a>.

###3. Descriptions

The descriptions page provides plenty of space to enter the brief and full descriptions as well as optional notes.

<i>Collected data is for metadata records.</i>

<span class="workflow_image" id="descriptions_page"><img src="{{ site.JB.BASE_PATH }}/images/description.png" /></span>
Figure 3: Screenshot of project creation page <a onclick="enlarge('descriptions_page');">[Enlarge]</a>.

###4. Information

Collects the bulk of metadata (information about the collected research data) for the ReDBox record such as keywords, research codes, dates, location and other related information.

Some fields require additional priveleges to view such as citation and entering a custom license, this keeps the form as simple as possible for the majority of users.

If a research grant was selected the date from and date to fields will be prefilled (when available).

<i>Collected data is for metadata records (Location may be used to pre-fill dataset locations).</i>

<span class="workflow_image" id="metadata_page"><img src="{{ site.JB.BASE_PATH }}/images/information.jpg" /></span>
Figure 4: Screenshot of project creation page <a onclick="enlarge('metadata_page');">[Enlarge]</a>.


###5. Methods

The methods page sets up ways of collecting data (data sources), what the data is or its type (data configuration) as well as collecting the methods name (used to generate record titles of associated datasets) and description (added as a note description to records).

Adding methods uses a simple wizard (shown in figure 5 below) that allows selection of a method template.  Method templates pre-fill any/all data in methods and their associated datasets.

<span class="workflow_image" id="create_method"><img src="{{ site.JB.BASE_PATH }}/images/create_method.png" /></span>
Figure 5: Screenshot of method creation page (method templates are hidden by default) <a onclick="enlarge('create_method');">[Enlarge]</a>.

The type of data being collected allows configuration of what data is collected and how that data is indexed:
* Most methods will store raw data as a file and index specific information so it is searchable.
* Standardised fields are provided for common data types (eg. temperature, humidity, etc).  
* Using the standardised fields will make the indexed data searchable globally within the data storage.
* Data configuration allows full configuration of the data types as well as how to display the fields in a web form.

Selection of the data source specifies how data will be ingested but configuration of the data source is done in the datasets step.

<i>Collected data is used for metadata records, service records and data ingestion.</i>

<span class="workflow_image" id="methods_page"><img src="{{ site.JB.BASE_PATH }}/images/methods.png" /></span>
Figure 6: Screenshot of method page <a onclick="enlarge('methods_page');">[Enlarge]</a>.

###6. Datasets

Each dataset represents an individual collection of data with an associated metadata record (metadata record generation can be disabled).

Adding datasets uses a simple wizard where the data collection method is selected as shown in figure 7 below.

<span class="workflow_image" id="create_dataset"><img src="{{ site.JB.BASE_PATH }}/images/create_dataset.png" /></span>
Figure 7: Screenshot of dataset creation page <a onclick="enlarge('create_dataset');">[Enlarge]</a>.

The dataset page collects the following data:
* Whether to create a metadata record and when the record should be published.
* Location of the data, the location may be a set location or an offset from a location where that is more relevent.  For example it is more relevent that the sensor shown is 1m from the base of the artificial tree.
* Configuration of the data source.

Each data source is configured differently but will usually require the data location, when to sample and how to process the found data.

<i>Collected data is mainly for data ingestion but the location is used for the metadata records.</i>

<span class="workflow_image" id="datasets_page"><img src="{{ site.JB.BASE_PATH }}/images/dataset.png" /></span>
Figure 8: Screenshot of datasets page <a onclick="enlarge('datasets_page');">[Enlarge]</a>.

###7. Submit

Submit provides full project validation and an overview of the generated records and data ingesters.  The project has four states:
* Open - The initial state when a project is created, the creator and administrators have read/write access.  The creator can also share parmissions with other users.
* Submitted - When the project is submitted by the creator it is ready to be reviewed by the administrators and either approved or reopened.  A project can only be submitted when there are no validation errors.  In the submited state creators have read access and administrators have read/write access.
* Approved - When an administrator approves the project:
	* Metadata records are exported to ReDBox.
	* Data ingesters are configured and started.
	* The project can no longer be modified, the creator and administrators only have read access.
* Disabled - This state represents the end of the project, when an administrator disables an approved project it disables all ingesters (no more data will be ingested).

The generated record for each dataset can be viewed, edited or reset.  Viewing a dataset record is exactly the same as general details, descriptions and information all on a single form. 

<span class="workflow_image" id="submit_page"><img src="{{ site.JB.BASE_PATH }}/images/submit.png" /></span>
Figure 9: Screenshot of project creation page <a onclick="enlarge('submit_page');">[Enlarge]</a>.

What now?
=========
Once the project has been setup, submitted and approved:
* Metadata records are create and exported to ReDBox, which then publishes them nationally to Reseach Data Australia (RDA). This is targetted advertising of the research you have collected, gaining you recognition!
* Data is streamed directly from the artificial tree into the database.


