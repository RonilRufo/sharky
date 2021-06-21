# sharky

_**TODO**: point these links to the correct URLs once CI is activated for this project_

- [![build status](https://dev.izeni.net/ci/projects/_TODO_/status.png?ref=master)](https://dev.izeni.net/ci/projects/_TODO_?ref=master) @ [master](https://dev.izeni.net/_TODO__PROJECT_GROUP__TODO_/sharky/blob/master/README.md)
- [![build status](https://dev.izeni.net/ci/projects/_TODO_/status.png?ref=develop)](https://dev.izeni.net/ci/projects/_TODO_?ref=develop) @ [develop](https://dev.izeni.net/_TODO__PROJECT_GROUP__TODO_/sharky/blob/develop/README.md)


## Setting up a development environment

### [Recommended development tools/aliases][recommended-development-tools]

[recommended-development-tools]: https://dev.izeni.net/izeni/izeni-django-template/wikis/recommended-development-tools

### Classic method

_(Note: make certain you are using **python3** for this - python2 is no longer supported, and will not work!)_

1. Install the database, build-dependencies, & python requirements for the project:

    _(Note: if you aren't using a virtualenv, then substitute `pip3` for `pip` below!)_

    ```bash
    sudo apt-get install postgresql
    sudo apt-get build-dep pillow psycopg2
    pip install -r requirements.txt
    ```

1. Create the database:

    ```bash
    echo "CREATE USER sharky WITH PASSWORD 'sharky'; CREATE DATABASE sharky OWNER sharky; ALTER USER sharky CREATEDB;" | su postgres -c psql
    ```

1. Migrate the database:

    ```bash
    ./manage.py migrate
    ```

1. Create a superuser to access the admin:

    ```bash
    ./manage.py createsuperuser
    ```

1. Start a locally-accessible development webserver:

    ```bash
    ./manage.py runserver 0.0.0.0:8000
    ```

### Docker method

1. Build and start the stack:

    ```bash
    docker-compose up -d
    ```

1. Create a superuser to access the admin:

    ```bash
    docker-compose run --rm backend ./manage.py createsuperuser
    ```

## Typical development tasks

### Admin

Visit the admin in your browser at: [http://0.0.0.0:8000/admin](http://0.0.0.0:8000/admin)

### Run tests

Use the Django test framework to run project tests:

```bash
./manage.py test
```

-or-

```bash
docker-compose run --rm backend ./manage.py test
```

### Django shell

Enter a Django shell:

```bash
./manage.py shell
```

-or-

```bash
docker-compose run --rm backend ./manage.py shell
```

### Postgres shell

Enter a PostgresQL shell connected to the project database:

```bash
su postgres -c "psql sharky"
```

-or-

```bash
docker exec -it sharky_database_1 su postgres -c "psql sharky"
```

## Gitlab CI troubleshooting

If you have problems getting CI tests to pass, here's an easy way to run (roughly) all the same code and tests that Gitlab CI will run. This will then dump you into a shell in that container so you can investigate more fully.

_(Yes, this uses python:3.4 intentionally - the image that GitLab CI uses is built on 3.4. We'll update this when that changes.)_

```bash
docker run -it --rm -v `pwd`:/app python:3.4 bash -c "cd /app && bash .gitlab-ci.sh && python manage.py test && bash"
```
