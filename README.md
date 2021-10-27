# LDSA Portal

Your friendly neighborhood LDSA Academy portal.


## Local development

### Setup

The first time you run this you need to create the database and a super user.

Start by running the following command:

```bash
docker-compose run --rm django ./manage.py migrate
```

Then create an admin:

```bash
docker-compose run --rm django ./manage.py createsuperuser
```

This will prompt you for a user, password and email. Once you have these
you can access the admin site (see below) and create the remaining
entities.

### Creating entities

Create an instructor:

```
docker-compose run --rm django ./manage.py create-instructor \
  -u 'ana' \
  -p 'ana1234' \
  -e 'ana@lisbondatascience.org' \
  -n 'Ana' \
  -git 'Ana' \
  -s 'U21392ANA' \
  -g 'female' \
  -t 'regular' \
```

Create a student:

```
docker-compose run --rm django ./manage.py create-student \
  -u 'joao' \
  -p 'joao1234' \
  -e 'joao@lisbondatascience.org' \
  -n 'Joao' \
  -git 'Joao' \
  -s 'U21392JOAO' \
  -g 'male' \
  -t 'regular' \
```

Create a specialization:

```
docker-compose run --rm django ./manage.py create-spec \
  -c S01 \
  -n 'Bootcamp'
```

Create a unit:

```
docker-compose run --rm django ./manage.py create-unit \
  -s S01 \
  -c SLU01 \
  -n 'SLU01 - Pandas' \
  -due '2020-04-10' \
  --open
```

### Seeding the db

To seed the entire db with pre-arranged data, run:

```
docker-compose run --rm django ./scripts/db_seed.sh
```

You can then login with any of the users created, for which the passwords are `<user>1234` or
with the admin (user `admin`, password `123`)

### Starting

```bash
docker-compose up
```
And then access the website in:
http://localhost:8000

And the admin site in:
http://localhost:8000/admin/

Emails are sent to:
http://localhost:8025

Admin creds
* username: admin
* password: 123

Entering the container:
```bash
docker-compose exec django bash
source docker/production/django/entrypoint
```

#### Temporarily deprecated - data initialization from fixtures

Currently the data under `fixtures/initial.yaml` is out of date and as such the
following command is deprecated

```bash
docker-compose run --rm django ./manage.py loaddata fixtures/initial.yaml
```

### Test submissions

To test submissions get the hash for the exercise notebook using ldsagrader add
it to the unit.
Then create a student user with your github username and add the deploy key to
your repository.




### Running tests

```bash
docker-compose run tests
```


### Updating Fixtures

```bash
docker-compose run --rm django ./manage.py dumpdata --format=yaml --output=fixtures/initial.yaml
```

### Starting over
```bash
docker-compose rm
docker volume rm portal_local_postgres_data
docker volume rm portal_local_postgres_data_backups
```

## Deploy

1. Build the container
    * Use the commit hash that is on master to tag the image
        ```bash
        docker build -f docker/production/django/Dockerfile -t ldssa/django:<commit hash> .
        ```
1. Push the container
    ```bash
    docker push ldssa/django:<commit hash>
    ```
1. Set the new commit hash in the [portal-deployment repo](https://github.com/LDSSA/portal-deployment)
    * Set the commit hash in the following files
        ```bash
        portal-staging/django-staging-deployment.yaml
        portal/django-deployment.yaml
        portal/scheduler-deployment.yaml
        portal/simulator-deployment.yaml
        ```
1. Tell kubernetes to run the new container
    ```bash
    cd portal-deployment
    kubectl apply -f portal
    ```
    * You might get this warning, no need to worry
        * `The Service "django" is invalid: spec.ports[0].nodePort: Forbidden: may not be used when `type` is 'ClusterIP'`
    * Make sure the old containers are killed and the new containers are running
        * `watch kubectl get pods`
    * If for some reason the containers don's start or the deployment goes wrong, just apply the configuration with the old commit hash
1. Running migrations
    * If you’ve changed the django models, then you’ll need to run migrations
    ```bash
    kubectl exec -ti $(kubectl get pods -l app=django -o custom-columns=:metadata.name | tail -n +2 | head -1) -- bash
    source docker/production/django/entrypoint
    ./manage.py showmigrations | grep '\[ \]'
    ./manage.py migrate
    ```
