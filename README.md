# LDSA Portal

Your friendly neighborhood LDSA Academy portal.


## Local development

The first time you need to create the database and a super user.
```bash
docker-compose run --rm django ./manage.py migrate
docker-compose run --rm django ./manage.py loaddata fixtures/initial.yaml
```

To test submissions get the hash for the exercise notebook using ldsagrader add
it to the unit.
Then create a student user with your github username and add the deploy key to
your repository.

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

## Build & push

```bash
docker build -f docker/production/django/Dockerfile -t ldssa/django:<commit hash> .
```

```bash
docker push ldssa/django:<commit hash>
```


