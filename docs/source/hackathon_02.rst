Hackathon 02 Checklist
======================

For the hackathon 02, the original data is split between a train and test dataset. The training data is split between multiple data sources:

* Files with multiple formats, wrong encodings, etc (this is done to make the students work in order to get clean data). An example of how this was done can be found `here <https://github.com/LDSSA/batch5-instructors/blob/71ae50aa3c17800008ae6480b95aa48ed310d20b/S02%20-%20Data%20Wrangling/HCKT02%20-%20Data%20Wrangling/portal/files_data/Split%20dataset.ipynb>`_.
* Data to be deployed to an api, a website and a database.

You can split the features and/or observations (ids + features) into different sources (files, api, website, and database).


What is needed from instructors for Hackathon 02
------------------------------------------------

An example of this can be found in this `link <https://github.com/LDSSA/batch5-instructors/pull/338/files>`_.

* A document containing the problem description and prompt, such as https://docs.google.com/document/d/1ty9cWsiVuUUho8oMmQVe0JfO1Y04b-yympg0PuvK_Hg/edit#heading=h.ejeq9rg4kyaz

* A merge request (from a branch called “HCKT02 - Data Wrangling” as described here https://github.com/LDSSA/batch6-instructors#122-branch-names-and-triggers), with a folder “S02 - Data Wrangling/HCKT02 - Data Wrangling/” containing
    * A Readme linking to the document containing the problem description and prompt such as https://github.com/LDSSA/batch5-instructors/blob/main/S02%20-%20Data%20Wrangling/HCKT02%20-%20Data%20Wrangling/README.md
    
    * A folder called ``data``, containing
        * Multiple files with data for the students to wrangle
        * A ``sample_submission.csv`` file containing a sample submission with the same IDs in the test dataset
        * A file called ``test.csv`` containing the test dataset with no labels, only features, for example https://github.com/LDSSA/batch5-instructors/blob/71ae50aa3c17800008ae6480b95aa48ed310d20b/S02%20-%20Data%20Wrangling/HCKT02%20-%20Data%20Wrangling/data/test.csv
    
    * A folder called porta containing
        * A folder called ``api_data`` containing a csv with the data to be made available in the api
        * A folder called ``database_data`` containing a csv with the data to be made available in the database
        * A folder called ``website_data`` containing a csv with the data to be made available in the website
        * A ``score.py`` file containing the code to score a submission. Generally this template can be used an only the scoring function needs to be changed (the highlighted line) https://github.com/LDSSA/batch5-instructors/blob/main/S02%20-%20Data%20Wrangling/HCKT02%20-%20Data%20Wrangling/portal/score.py#L45
        * A file called ``data`` (with no extension) containing the test data (ids and labels) in csv format. This file contains the labels for the file ``test.csv``. For example https://github.com/LDSSA/batch5-instructors/blob/71ae50aa3c17800008ae6480b95aa48ed310d20b/S02%20-%20Data%20Wrangling/HCKT02%20-%20Data%20Wrangling/portal/data
    * A ``requirements`` file like https://github.com/LDSSA/batch5-instructors/blob/main/S02%20-%20Data%20Wrangling/HCKT02%20-%20Data%20Wrangling/requirements.txt
