FROM --platform=linux/amd64 python:3.12
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt update && apt upgrade -y
ENV NODE_MAJOR=20
RUN mkdir -p /etc/apt/keyrings; \
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg; \
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list; \
apt update && apt install nodejs -y;
RUN apt install postgresql -y
RUN psql --version
WORKDIR /code
COPY . /code/
RUN pip install -r requirements_for_test.txt
RUN npm install
EXPOSE 8001
