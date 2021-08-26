FROM python:3.9
ARG     POETRY_VERSION=1.1.8

RUN     apt-get update -qq && \
        apt-get install -y -qq --no-install-recommends 'git=1:2.20.1-2+deb10u3' && \
        rm -rf /var/lib/apt/lists/* && \
        true

ENV     PYTHONUNBUFFERED=1 PYTHONPYCACHEPREFIX=/var/lib/pycache PATH=/root/.poetry/bin:$PATH
RUN     mkdir /var/lib/pycache

ADD     https://raw.githubusercontent.com/python-poetry/poetry/${POETRY_VERSION}/get-poetry.py /get-poetry.py
RUN     python /get-poetry.py --version ${POETRY_VERSION} --yes --no-modify-path && \
        poetry config virtualenvs.create false

COPY    pyproject.toml poetry.lock /sharky/
WORKDIR /sharky/
RUN     poetry install --no-interaction --no-ansi -E prod --no-dev --no-root

#       Install again after copying whole source, so that `sharky` and `apps` are installed.
COPY    . /sharky/
RUN     poetry install --no-interaction --no-ansi -E prod --no-dev

ARG     CI_COMMIT_SHA=
ARG     CI_COMMIT_REF_NAME=
ARG     CI_PIPELINE_ID=
ARG     THIS_IMAGE=
ENV     CI_COMMIT_SHA=${CI_COMMIT_SHA} \
        CI_COMMIT_REF_NAME=${CI_COMMIT_REF_NAME} \
        CI_PIPELINE_ID=${CI_PIPELINE_ID} \
        THIS_IMAGE=${THIS_IMAGE}

CMD        ["./server/server.sh"]
