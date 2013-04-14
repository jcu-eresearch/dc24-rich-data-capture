---
layout: post
title: "Real User Testing &#38; Feedback"
description: "What test users thought of our interface, its usability and functionality."
author: "lauren"
category: 
tags: [andsUserAcceptance, andsOutputs, andsProduct, andsApps,  fundedByAustralianNationalDataService, DIISRTE, EnMaSSe, DC24, Environmental Monitoring and Sensor Storage, richDataCapture]
---
{% include JB/setup %}

EnMaSSe (Environmental Monitoring and Sensor Storage) has two main user groups:
* Researchers that are looking for a way to store their data, these users require an easy-to-use system that has a high level of flexibility focused on entering data.
* Researchers that are searching for data to use in their own research are concerned with the quality of data (and metadata) and how easy it is to access the data.

These two user groups and their requirements have been explained in more detail on the [EnMaSSe developer blog]({{ site.JB.BASE_PATH }}/2012/08/27/key-factors-customers-will-use-to-judge-the-value-of-our-product).

Testing & Requirements Gathering Process
========================================

Requirements gathering began with researching use cases and researcher workflows from all appropriate sources that we could find, and continued with approximately fortnightly clarifications and demonstrations over the duration of the project.  This processes has been further documented in our [Testing & Feedback blog]({{ site.JB.BASE_PATH }}/2012/12/12/testing--feedback/).

In early April 2013 we conducted user testing of the EMASSE user interface on two likely end users.  To test the effectiveness of the interface we gave a generalised verbal overview of data-handling issues faced by researchers (such as impermanent storage, difficulty sharing data, difficulty attributing methods to data, management of multiple interrelated project data) and explained how this tool attempts to solve these issues.  We then sat with the researcher while they interacted with the interface to monitor whether this tool was accessible to the end user in its present state.

User 1 was tested a full week before User 2.  This allowed for all comments to be addressed and solutions to be suggested and implemented where possible before commencement of User test 2.  In this way we hoped to assess the success of our potential solutions and to address the problems, and found this approach to be very successful.

Our test users
==============

**User** 1 was a PhD student and Research Assistant at JCU working on a project that uses microclimate data collected from multiple locations along both latitudinal and altitudinal gradients and stored in a large database to construct fine-grained climate layers.  We expected this user to represent researchers who have collected large amounts of data under the same methodology in the past.

**User 2** was a Research Assistant at JCU who had used ibuttons to collect temperature from multiple types of data to examine available microclimate to small vertebrates. We expected this user to represent researchers who use complex methodology.  User 2 was also experienced in both using and sharing repository data.

Other typical users, particularly those who will begin to use next-generation sensor technology, have been very involved throughout the whole project and thus were not suitable candidates for user testing.

The “overwhelming” theme
========================

Let’s get this out of the way: User test 1 was overwhelming for User and Developer alike.  The overwhelming theme of User test 1 was that all of the functionality appeared to be there without enough explanation as to how these functions could and should be used.  This was supported by the fact that after a lot of conversation, User 1 understood the purpose and use of the vast majority of the interface.

However, even once we had attempted to address the overwhelming lack of explanation, User 2 struggled to identify how to use the tool for the specific test case... until further explanation was provided.  

Therefore most comments, suggestions and changes outlined in detail below revolved around how to communicate functionality succinctly, rather than on changes to functionality.

We took this to be positive feedback.

Create Project/General
======================

This page is designed to speed up the process of metadata creation.  Users are given the option to pre-fill much of the metadata with either associated grant information or pre-defined templates for the organisation.  

What Succeeded
---------------

After updating the templates based on feedback from User 1, User 2 checked and unchecked the textbox, determined templates were irrelevant, then filled out all following fields and moved on to create a project.  This solution was deemed successful.

What We Learned
---------------

Upon selecting ‘New Project’, User 1 was fronted with this:

![Original display of templates on project creation.]({{ site.JB.BASE_PATH }}/images/template_old.png)

This upfront focus on templates generated confusion for the user who was considering a single discrete project rather than the many projects undertaken by some of the larger end-user organisations who have quite different needs.

We decided to circumvent this state of confusion by setting the default to a blank template and hiding template choices behind a checkbox, as well as providing better descriptions of the pre-fill options available.

Descriptions
============

The “Descriptions” tab simply allows the addition of brief, full and note descriptions for the purpose of generating metadata records.

What Succeeded
---------------

The importance of attributing a full project description to data became very clear to both users.  They liked that this detailed description would only need to be constructed once and would never need to be pasted into the multiple metadata records.  User 1 said the fields on this tab prompted careful thought about all information relevant to the data.

What We Learned
---------------

User 2 commented that it was difficult to write a separate full description of the project when methods are described elsewhere, but very much liked that there was a dedicated methods section.  With a few suggestions as to what information could be added to a full description, User 2 liked that aims and expected outcomes of the project could be fleshed out in detail that is typed up once and permanently attached to all related datasets.

Information
===========

Additional information, such as SEO codes, FOR codes, publications and attachments can be added here.

What Succeeded
--------------

This page was easy to use for both users and both recognised the value in the ability to attribute the available fields to data.


Methods
=======

Within a single project, multiple methods may be used to collect different relevant datasets.

This tab allows users to define multiple methods of data-collection each configuring how:
* Data will be entered into storage.
* Data will be stored and indexed for searching.
* Data will be displayed.

What Succeeded
---------------

Users understood that multiple datasets could be attached to a single method and liked that this method would only need to be typed up once.

What We Learned
---------------

We learned that giving users the option to configure their data through an online interface is difficult.  It was at the data configuration stage that both users became unsure.  We provided several ‘standard’ configurations, and User 2 pointed out that there was no way to see what these standard configurations were.

Additionally, we learned that describing different data sources in succinct, common english was not possible.  We trialled succinct explanations of sources without further explanation on User 1, but the only explanation that was readily understood was ‘pull data from external source’.  Therefore, we kept our succinct wording of the options, but added a lengthy description under the help menu.  User 2 found these descriptions and could use them to decide which method of sourcing the data was relevant.

We were also faced with some difficulty here in terms of what users expected to happen when they selected an option from the data-sourcing radio-buttons.  Both users expected to see an option to undertake some further action on the methods page.  However, as data sourcing must be performed per-dataset, we could not add the actions the users expected to find on the methods page.  We resolved this issue by informing User 2 that selecting a particular option would generate fields that would need to be filled on the datasets page.  User 2 understood that urls needed to be supplied on a per-dataset basis, and therefore understood why the action would be found on the datasets page.

Datasets
========

Under each method, many different datasets may be collected, usually at different locations.

What Succeeded
---------------

Users were able to add data source and location to datasets with ease.

What We Learned
---------------

User 2 became confused by some fields available on this page, and could not interpret them.  We decided these fields were mostly applicable to administrators and could be replaced with plain text descriptions, the advanced options were hidden behind a checkbox making the complexity and user expectations clear.

Submit
======

The submission tab enables users to review all metadata records and datasets that are to be created as well as controls to submit the project for approval.

What Succeeded
---------------

The ability to view final per-dataset metadata records was appreciated.

What We Learned
---------------

There was a bug in the population of redbox records - User 2 commented on the expectation that these fields would be filled.

Individual User Experiences
===========================

Interface design and interaction (ie. navigating between different types of fields)
-----------------------------------------------------------------------------------

**User 1** only fumbled a little with unfamiliar and unexpected features such as name auto-completion; inputting locations on a map; etc., but followed error messages and corrected the mistakes quickly.  

**User 2** was familiar with similar systems and features and commented on the ease of use created through this familiarity.

We determined that only very minor tweaks were required to increase the overall ease of use of the interface fields.

Conclusion
==========

We considered that the users needs were met in terms of functionality, and have been met in terms of required explanations of that functionality upon availability of a user guide.  

We were encouraged by the improved responses of User 2 after the amendments we made in response to the comments of User 1 and now feel that the within-interface descriptions of functionality adequately fulfill user needs.  

Further feedback will be sought during continued development and the first weeks of deployment.








