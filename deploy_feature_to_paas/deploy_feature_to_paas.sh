GITBRANCH=$(git branch --show-current)
NAME=${USER}
NAME="${NAME:0:4}"
CF_SPACE_NAME="${NAME}_${GITBRANCH}"
DIR="$(dirname "${BASH_SOURCE[0]}")"  # Get the directory name
DIR="$(realpath "${DIR}")"    # Resolve its full path if need be
APPNAME="amp-${CF_SPACE_NAME}"
URL="${APPNAME//_}"
PARENT_DIR="$(dirname "$DIR")"
RANDOM_PASSWORD="$(openssl rand -base64 12)"
source "${PARENT_DIR}/.env"

if [ "$1" = "up" ]
then
  echo "Setting up testing environment"
  cf create-space "$CF_SPACE_NAME"
  cf target -s sandbox
  cf share-service a11ymon-postgres -s ${CF_SPACE_NAME}
  cf target -s "$CF_SPACE_NAME"
  cf create-service postgres small-11 monitoring-platform-default-db
  # Has to wait to ten minutes to allow the database to spin up
  sleep 600

  echo "---
applications: 
- name: "${APPNAME}"
  memory: 512M
  instances: 1
  buildpacks:
    - python_buildpack
  services:
    - monitoring-platform-default-db
    - a11ymon-postgres
  env:
    DEBUG: FALSE
    ALLOWED_HOSTS: '${URL}.london.cloudapps.digital'
    DISABLE_COLLECTSTATIC: 1
    SECRET_KEY: '${SECRET_KEY}'
" > "${DIR}/manifest.yml"
  cf push -f "${DIR}/manifest.yml"
  echo "SSH into instance with cf ssh amp-rich_int_new_a11ymon_data"
  echo "Login into Python shell with /tmp/lifecycle/shell"
  echo "Create superuser with:"
  echo "echo \"from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@email.com', 'admin@email.com', '${RANDOM_PASSWORD}')\" | python manage.py shell"
  echo "email is admin@email.com and password is ${RANDOM_PASSWORD}" 
else
  echo "Tearing down testing environment"
  cf delete-space -f "$CF_SPACE_NAME" 
  sleep 600
  cf delete-space -f "$CF_SPACE_NAME" 
fi
