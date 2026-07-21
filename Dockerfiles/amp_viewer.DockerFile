FROM --platform=linux/amd64 python:3.12-slim-bookworm

ARG NODE_MAJOR=20

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        gnupg \
        libpq-dev \
        make \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements_for_test.txt ./
COPY requirements.txt ./
RUN python -m pip install --requirement requirements_for_test.txt

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /code

USER appuser

EXPOSE 8001

CMD make static_files_process \
    && python manage_report_viewer.py collectstatic --noinput \
    && exec waitress-serve \
        --port=8001 \
        --threads=5 \
        report_viewer.wsgi:application