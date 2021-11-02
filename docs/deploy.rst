Deploy
========

#. Build the container
    * Use the commit hash that is on master to tag the image::

        docker build -f docker/production/django/Dockerfile -t ldssa/django:<commit hash> .

#. Push the container::

    docker push ldssa/django:<commit hash>
    
#. Set the new commit hash in the [portal-deployment repo](https://github.com/LDSSA/portal-deployment)

    * Set the commit hash in the following files
    
        portal-staging/django-staging-deployment.yaml
        portal/django-deployment.yaml
        portal/scheduler-deployment.yaml
        portal/simulator-deployment.yaml

#. Tell kubernetes to run the new container.
    * Run::

        cd portal-deployment
        kubectl apply -f portal
    
    * You might get this warning, no need to worry::
    
        The Service "django" is invalid: spec.ports[0].nodePort: Forbidden: may not be used when `type` is 'ClusterIP'

    * Make sure the old containers are killed and the new containers are running::

        watch kubectl get pods

    * If for some reason the containers don's start or the deployment goes wrong, just apply the configuration with the old commit hash
    
#. Running migrations

    * If you’ve changed the django models, then you’ll need to run migrations::

        kubectl exec -ti $(kubectl get pods -l app=django -o custom-columns=:metadata.name | tail -n +2 | head -1) -- bash
        source docker/production/django/entrypoint
        ./manage.py showmigrations | grep '\[ \]'
        ./manage.py migrate

