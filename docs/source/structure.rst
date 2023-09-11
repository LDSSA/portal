Project Structure
==================

File Structure
--------------

Here are a few of the more important project directories.

* ``.devcontainer/`` - Contains *VS Code* development containers config.
* ``.envs/.local/`` - Environment files to run the project locally.
* ``.vscode/`` - *VS Code* config.
* ``config/`` - Project root config.
* ``docker/`` - Dockerfiles.
* ``docs/`` - Portal documentation.
* ``portal/`` - Source code.
* ``requirements/`` - Local and production project requiremtnts.
* ``scripts/`` - Helper scripts.


Services
--------

Services provided and consumed by the portal.

* ``portal`` - Portal website.
* ``backoffice`` - Portal backoffice.
* ``simulator`` - Service that sends capstone datapoints to student API's.
* ``scheduler`` - Service to run periodic tasks.
* ``db`` - Portal database (**postgres**).
* ``caching``  - Portal caching, redis in production.
* ``mail server`` - Elasticemail for production and mailhog locally.
* ``git repos`` - Exercise repositories.
* ``ci`` - Exercise validation and producing exercise docker images.
* ``docker image repository`` - Storing docker images.
