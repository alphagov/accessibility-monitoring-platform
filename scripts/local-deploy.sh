pip install --upgrade pip && pip install pipenv && pipenv install -d && npm i
pipenv lock -r > requirements.txt
gulp build
cf push -f manifest-prod.yml