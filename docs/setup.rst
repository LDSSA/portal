Project Setup
===============

.. image:: assets/learning_units.png

Repositories & CI
------------------

The portal requires two repositories to be set up, the instructors repository 
and the students repository.
The CI pipeline on the instructors repository will:

* Validate exercises
* Post the exercise checksum to the portal
* Create a docker image for the exercise
* Remove exercise solutions and place it on the students repository

This requires the following environment variables to be setup in the CI:

* `DOCKER_PASS`
* `DOCKER_USER`
* `PORTAL_CHECKSUM_URL_TEMPLATE`
* `PORTAL_HACKATHON_URL_TEMPLATE`
* `PORTAL_TOKEN`
* `STUDENT_REPO`

Admissions requires it's own repositories setup.

Portal Variables
------------------

Portal setup is done mostly through its kubernetes configmap.
The variables that change according to the batch are:

* `STUDENT_REPO_NAME`
* `DJANGO_AWS_STORAGE_BUCKET_NAME`
* `SLACK_WORKSPACE`

The `PORTAL_TOKEN` mentioned in the previous section is a Django authentication
token generated for the user setup in `GRADING_USERNAME`.
