# Alpine image has no support for ODBC-drivers
#FROM python:3.8-alpine
#RUN apk update
#RUN apk add build-base gcc libffi-dev musl-dev mariadb-connector-c-dev unixodbc-dev unixodbc

FROM python:3.8-slim-buster

# build variables.
ENV DEBIAN_FRONTEND=noninteractive

# install Microsoft SQL Server requirements.
ENV ACCEPT_EULA=Y
RUN apt-get update -y && apt-get update \
  && apt-get install -y curl gcc g++ gnupg unixodbc-dev libffi-dev musl-dev unixodbc-dev unixodbc libmariadb-dev

# Add SQL Server ODBC Driver 17 for Ubuntu 18.04
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
  && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends --allow-unauthenticated msodbcsql17 mssql-tools \
  && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile \
  && echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc



# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# copy every content from the local file to the image
COPY . /app

RUN echo 'export PATH="$PATH:/app"'

# OPTION 1: Voor gebruik van de Flask webserver
#ENTRYPOINT [ "python" ] 
#CMD ["app.py" ]

# OPTION 2: gunicorn, standaard workers
#CMD ["gunicorn", "--timeout", "600", "--workers", "5", "--bind", "0.0.0.0:443", "app:app"]

# OPTION 3: gunicorn met gevent
CMD ["gunicorn", "--timeout", "600", "--worker-class", "gevent", "--workers", "5", "--bind", "0.0.0.0:443", "patched:app"]

# OPTION 4: gunicorn met Letsencrypt certificates
#CMD ["gunicorn", "--timeout", "600", "--worker-class", "gevent", "--workers", "5", "--bind", "0.0.0.0:443", "--certfile", "/etc/letsencrypt/certificates/fullchain.pem", "--keyfile", "/etc/letsencrypt/certificates/privkey.pem", "patched:app"]



EXPOSE 443

