# interventie2
De Autoriteit Financiële Markten (AFM) heeft een werkwijze ontwikkeld voor de selectie van informele interventieinstrumenten. Deze werkwijze bestaat uit een gefaciliteerde sessie, software, een vragenlijst en een catalogus van instrumenten. Door al deze materialen vrij beschikbaar te maken en te delen met andere toezichthouders, willen wij een uitwisseling van methoden op gang brengen waarvan alle toezichthouders profiteren.

# Installatie met Docker op een Linux server
Installeer Linux op een machine, en installer vervolgens Docker. Daarna kan je de volgende stappen volgen om de app te installeren als webserver. 

# Get certificate for the server
apt-get install certbot
ufw allow 80
certbot certonly --standalone --preferred-challenges http -d <url>
ufw allow 443

# Create docker network
docker network create -d bridge my-network

# MariaDB image
docker run --name mariadb -e MYSQL_ROOT_PASSWORD=<your-root-password> --network my_network -d mariadb:latest

# phpMyAdmin image
docker run --name phpmyadmin -d --network my_network --link mariadb:db -p 8081:80 phpmyadmin

# Create database and new user for interventie2 in phpmyadmin
Go to <ip-address>:8081
Create new database:    interventie2
Username:               interventie2_user
Password:               <your-user-password>
- Make sure the new user has full privileges for the new database.
- Stop phpmyadmin when you no longer need it.
docker stop phpmyadmin

# Clone interventie2 image from github
git clone https://github.com/FilipVdBergh/interventie2.git

# Copy a settings.cfg file to the parent of the interventie2 folder containing:
SECRET_KEY=SECRETKEY
APP_NAME=interventie2
ALLOW_DB_INIT=True
ALLOW_CATALOG_VIEW=False
ALLOW_CONTACT=False
MAINTAINER=interventieteam
MAINTAINER_EMAIL=interventie@afm.nl
SQLALCHEMY_DATABASE_URI=mysql://interventie2_user:<your-user-password>@mariadb:3306/interventie2

# Check the Dockerfile to see if the image will be built with the correct gunicorn options (in particular the references to the certificates)

# Build and run the comtainer with links to the settings.cfg file and to the certificates
- Replace <url> with your own domain in the command below.
docker build -t interventie2 .
docker run --name interventie2 --env-file /root/settings.cfg -p 443:443 --network my_network --link mariadb --mount type=bind,source=/etc/letsencrypt/live/<url>>/fullchain.pem,target=/etc/letsencrypt/certificates/fullchain.pem --mount type=bind,source=/etc/letsencrypt/live/<url>/privkey.pem,target=/etc/letsencrypt/certificates/privkey.pem -d interventie2

# To rebuild the image (create a bash script ./update)
docker stop interventie2
docker rm interventie2
rm -rf interventie2
git clone https://github.com/FilipVdBergh/interventie2.git
cd interventie2
docker build -t interventie2 .
docker run --name interventie2 --env-file /root/settings.cfg -p 443:443 --network my_network --link mariadb --mount type=bind,source=/etc/letsencrypt/live/<url>>/fullchain.pem,target=/etc/letsencrypt/certificates/fullchain.pem --mount type=bind,source=/etc/letsencrypt/live/<url>/privkey.pem,target=/etc/letsencrypt/certificates/privkey.pem -d interventie2

# Initialize database for first use
<url>/admin/initialize
- Login:             root:root
- Change the root password in the app and create a new user.
