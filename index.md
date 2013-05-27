---
layout: page
title: EnMaSSe
tagline: Environmental Monitoring and Sensor Storage
---
{% include JB/setup %}


# Welcome to EnMaSSe!

EnMaSSe allows researchers to setup projects that involve the collection of environmental monitoring data using sensors, 
video, audio recorders and/or manual observation methods. Once all the required information is provided the system configures
ingesters to suck up the data as it becomes available and stores it in the digital asset management system. In addition, it
creates a metadata record for each dataset (conforming to [ANDS](http://www.ands.org.au/ "Australian National Data Service")' 
standards).

<!--This project aims to build a collection of middleware that will allow for the automatic capture of sensor and video 
data and store this data along with the associated metadata in the JCU digital asset management system and the 
JCU Research Data Catalogue.-->

## Documentation
Documentation is available on the [Read-the-Docs EnMaSSe site](https://readthedocs.org/projects/tdh-rich-data-capture-documentation/).
* [User Guide](https://tdh-rich-data-capture-documentation.readthedocs.org/en/latest/enmasse-user.html)
* [Administrator's Guide](https://tdh-rich-data-capture-documentation.readthedocs.org/en/latest/enmasse-admin.html)
* [Developer's Guide](https://tdh-rich-data-capture-documentation.readthedocs.org/en/latest/enmasse-developer.html)

## Developer  Posts

<ul class="posts">
  {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>


## Finding the Source Code

All source code is available on our <a href="http://github.com/jcu-eresearch/TDH-rich-data-capture">github site</a>.
