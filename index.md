---
layout: page
title: TDH Rich Data Capture
tagline: 
---
{% include JB/setup %}


Welcome to the TDH Rich Data Capture site. This project aims to build a collection of middleware that will allow for the automatic capture of sensor and video data and store this data along with the associated metadata in the JCU digital asset management system and the JCU Research Data Catalogue.

## Developer  Posts

<ul class="posts">
  {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>


## Finding the Source Code

All source code is available on our <a href="http://github.com/jcu-eresearch/TDH-rich-data-capture">github site</a>.
