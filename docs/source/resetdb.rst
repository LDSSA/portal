Resetting the Database
========

Accessing the Database
------------------


In order to access the database, you need to use `kubectl`. 

#. You first configure AWS CLI to access the cluster:

    aws eks --region eu-west-1 update-kubeconfig --name portal-batch4 --profile ldsa-portal

#. You get the Django Pod name

    kubectl get pods

#. You log into the pod, much like we do when use SSH into it

    kubectl exec -it <POD_NAME> -- bash

#. Use Django to access the Database and handle the Django models. Be sure to have all the required settings in the environment variables.

    ./manage.py shell

Models to Delete
------------------

* `portal.users.models.User`
* `portal.academy.models.Specialization`
* `portal.users.models.UserWhitelist`
* `portal.capstone.models.Capstone`
* `portal.challenge.models.Challenge`
* `portal.hackathons.models.Hackathon`
