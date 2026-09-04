# Stage 1: PostgreSQL client binaries + their matching libpq runtime
FROM postgres:16-bookworm AS postgres-client


# Stage 2: application image
FROM python:3.12-slim-bookworm

ARG NODE_MAJOR=20

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# System/build dependencies.
#
# libpq-dev is still needed here for building Python PostgreSQL dependencies
# such as psycopg2. It also installs Debian's system libpq, but PostgreSQL
# command-line tools below are explicitly configured to use the libpq copied
# from the postgres:16-bookworm image instead.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        gnupg \
        libpq-dev \
        make \
    && rm -rf /var/lib/apt/lists/*


# ---------------------------------------------------------------------------
# PostgreSQL client
# ---------------------------------------------------------------------------
#
# Do NOT copy only /usr/lib/postgresql/16.
#
# The PostgreSQL client binaries from postgres:16-bookworm may have been built
# against a newer libpq than the one supplied by Debian Bookworm.
#
# Copy both the PostgreSQL 16 tooling AND the exact libpq runtime from the same
# source image so psql/pg_dump cannot accidentally load Debian's older libpq.

COPY --from=postgres-client \
    /usr/lib/postgresql/16 \
    /opt/postgresql/16

COPY --from=postgres-client \
    /usr/lib/x86_64-linux-gnu/libpq.so.5* \
    /opt/postgresql/lib/

ENV PATH="/opt/postgresql/16/bin:${PATH}" \
    LD_LIBRARY_PATH="/opt/postgresql/lib"


# Fail the Docker build immediately if PostgreSQL client linkage is broken.
#
# ldd should show:
#
#   libpq.so.5 => /opt/postgresql/lib/libpq.so.5
#
# and both version commands must execute successfully.
RUN echo "PostgreSQL client:" \
    && command -v psql \
    && psql --version \
    && pg_dump --version \
    && echo "libpq linkage:" \
    && ldd "$(command -v psql)" | grep libpq \
    && ldd "$(command -v psql)" \
        | grep -F "/opt/postgresql/lib/libpq.so.5"


# ---------------------------------------------------------------------------
# Node.js
# ---------------------------------------------------------------------------

RUN install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

WORKDIR /code

COPY requirements_for_test.txt ./
COPY requirements.txt ./

RUN python -m pip install --requirement requirements_for_test.txt

COPY package.json package-lock.json ./

RUN npm ci --verbose

COPY . .


# ---------------------------------------------------------------------------
# Runtime user
# ---------------------------------------------------------------------------

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /code

USER appuser

EXPOSE 8001


# ---------------------------------------------------------------------------
# Application startup
# ---------------------------------------------------------------------------

CMD make static_files_process \
    && python manage.py collectstatic --noinput \
    && python manage.py migrate \
    && python manage.py recache_statuses \
    && python manage.py send_reminders_email \
    && python manage.py clearsessions \
    && python manage.py axes_reset_logs --age 7 \
    && exec waitress-serve \
        --port=8001 \
        --threads=5 \
        accessibility_monitoring_platform.wsgi:application