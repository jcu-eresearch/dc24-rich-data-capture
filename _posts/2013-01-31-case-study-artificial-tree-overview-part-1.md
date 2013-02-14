---
layout: post
title: "Case Study: Artificial Tree Overview (Part 1)"
description: ""
author: "casey"
category: 
tags: [DIISRTE, fundedByAustralianNationalDataService, andsApps, DC24, richDataCapture]
---
{% include JB/setup %}

<style>
	.span8 {
		display: inline-block;
	}
	
	.span8 #sidebar li {
		//list-style-position: inside;
		position: relative;
		left: 30px;
		padding-right: 30px;
	}
	
	#sidebar #rest li {
		position: relative;
		left: 0px;
		padding-right: 0px;	
	}
	
	#sensor {
		margin: 20px !important;
		margin-left: 160px !important;	
		padding: 0px !important;
		line-height: 0;
	}

	#sensor img {
		width: 364px;
		height: 137px;
		border: none;	
		box-shadow: 0 0 10px #000;	
	}		
	
	#img-bar {
		display: inline-block;
		float: left;	
		clear: both;
		margin-right: 20px !important;
		line-height: 0;
	}	
	
	#img-bar img {
		width: 61px;
		height: 601px;
		box-shadow: 0 0 10px #000;
	}
	
	/*#img-bar:hover {
		width: 280px;
		height: 2722px;	
		z-index: 9999;
	}*/
	
	table {
		width: 100%;
	}
	
	th {
		font-weight: bolder;
		font-size: 1.1em;
	}
	td, th {
		border: 1px solid #555;
	}
</style>

Provisioning Interface Overview
======================================

Each <i>project</i> consists of project level metadata (information about the research data), <i>methods</i> of collecting data and <i>datasets</i> (individual collection of data).  

The primary purpose of methods is to define the data structure and the data source.  
* Data structures define how the data is represented in persistent storage and what is indexed.
* Data sources identify the way data is input into persistent storage (eg. streamed, web form).

Each dataset is an individual configuration of a method as well as a metadata record.

To make the whole process as easy as possible the following features have been implemented:
* Project templates allow all/any data for common projects to be pre-filled.
* Method+dataset templates allow all/any data within methods and their datasets to be pre-filled. 
* Duplicate project allows any existing project to be used as a template directly.
* Providing an associated grant will pre-fill as much information as possible (eg. people, project dates).

Once the project is configured, submitted and approved by the administrators:
* Project metadata (information about data) record will be created in [ReDBox](http://www.redboxresearchdata.com.au/).
* Each dataset will have a metadata record created in [ReDBox](http://www.redboxresearchdata.com.au/).
* Each dataset will provide functionality for data input directly into persistent storage.

What is the artificial sensor tree?
===================================

<div id="img-bar" title="Prototype artificial sensor tree installation">
	<img src="{{ site.JB.BASE_PATH }}/images/artificial_tree.jpg">
</div>

<span id="sidebar"></span>

The artificial sensor tree is a new environmental research tool being developed at [James Cook University (JCU)](http://www.jcu.edu.au) for measuring variations over rainforest canopy height.

Once development and testing is finished, **X** artificial sensor tree's will be deployed throughout the Daintree rainforest in cooperation with the [Daintree Rainforest Observatory (DRO)](http://eresearch.jcu.edu.au/projects/daintree-rainforest-observatory) project. 

The first prototype (illustrated left) is a 20m high carbon fibre tube with sensor stations (illustrated below) 1m apart including a calibrated temperature sensor and humidity sensor.  Each sensor is connected to the tree's controller (Arduino) over network cable (1-wire) which collects and sends the data to an internet file server. 

<div id="sensor" title="Prototype artificial sensor tree installation">
	<img src="{{ site.JB.BASE_PATH }}/images/sensor.jpg">
</div>

Each tree will be battery powered (with solar support) and equipped with radio transmitters to communicate with the central internet connected file server.

Why use this project for the case study?
----------------------------------------

* Complex enough to show how streaming sensors with quality metadata records scales with the minimum of work.  
* Similar research projects have in the past been conducted by researchers manually collecting data from each field sensor as well as manually setting up the associated metadata records.
* Complex enough to demonstrate the flexibility of our systems and illustrate the pros and cons of different configurations.
* Target audience for our project showing how the Rich Data Capture will be used in the future.

<span id="rest"></span>

Glossary
========

<table>
	<thead>
		<th>Word</th>
		<th>Description</th>
	</thead>
	<tr><td>Metadata</td><td>Information about the data.  Such as the location data is collected at or when it was collected.</td></tr>
	<tr><td>Project</td><td>Represents a research project or part thereof.  Choose a project so that many datasets can be created with similar configurations.</td></tr>
	<tr><td>Dataset</td><td>Single data collection which will have a ReDBox metadata record and a way of inputting data into persistent storage.</td></tr>
	<tr><td>Method</td><td>Way of collecting research data as well as how that data is stored and indexed in the persistent storage.  Each dataset is based on a method.</td></tr>
	<tr><td>Provisioning Interface</td><td>The Rich Data Capture web application that is used to provision the data ingestion and ReDBox metadata record creation.</td></tr>
	<tr><td>Ingester</td><td>Way of inputting data into persistent storage.  Eg. the file ingester regularly polls an external file server for new files.</td></tr>
	<tr><td>Sensor</td><td>An electronic device that collects data and in some way provides that data.</td></tr>	
</table>

<br />
<br />
Part 2 of the artificial tree case study will walk through the project setup.