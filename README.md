# interventie2
De Autoriteit Financiële Markten (AFM) heeft een werkwijze ontwikkeld voor de selectie van informele interventieinstrumenten. Deze werkwijze bestaat uit een gefaciliteerde sessie, software, een vragenlijst en een catalogus van instrumenten. Door al deze materialen vrij beschikbaar te maken en te delen met andere toezichthouders, willen wij een uitwisseling van methoden op gang brengen waarvan alle toezichthouders profiteren.

# Installatie met Docker op een Linux server
## Get certificate for the server
*https://www.digitalocean.com/community/tutorials/how-to-use-certbot-standalone-mode-to-retrieve-let-s-encrypt-ssl-certificates-on-ubuntu-16-04*

    apt-get install certbot
    ufw allow 80
    certbot certonly --standalone --preferred-challenges http -d YOURDOMAIN
    ufw allow 443

## Create docker network
    docker network create my_network

## MariaDB image
    docker pull mariadb
    docker run --name mariadb -e MYSQL_ROOT_PASSWORD=MyPasswordHere --network my_network -d mariadb:latest

## phpMyAdmin image
    docker pull phpmyadmin/phpmyadmin
    docker run --name phpmyadmin -d --network my_network –-link mariadb:db -p 8081:80 phpmyadmin

## Create database and new user for interventie2 in phpmyadmin
Database:               interventie2
Username:               interventie2_user
Password:               MyPasswordHere
- Make sure the new user has full privileges for the new database.
- Stop phpmyadmin when you no longer need it:
    docker stop phpmyadmin

## Clone interventie2 image from github
    git clone https://github.com/FilipVdBergh/interventie2.git

## Build and run interventie2 image
    docker build -t interventie2 .

### Environmental variables as arguments
    docker run --name interventie2 -e CONNECTION_STRING=mysql://interventie2_user:MyPasswordHere@mariadb:3306/interventie2 -p 443:443 --network my_network --link mariadb:db --mount type=bind,source=/etc/letsencrypt/live/interventie.sessie.online/fullchain.pem,target=/etc/letsencrypt/certificates/fullchain.pem --mount type=bind,source=/etc/letsencrypt/live/interventie.sessie.online/privkey.pem,target=/etc/letsencrypt/certificates/privkey.pem -d interventie2

### Environmental arguments in file
- -e INTERVENTIE_SETTINGS=./settings.cfg
- CONNECTION_STRING=mysql://interventie2_user:MyPasswordHere@mariadb:3306/interventie2

## Initialize database
<ip-address>/admin/initialize
- Login:             root:root
- Change the root password in the app and create a new user.
