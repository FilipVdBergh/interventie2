# interventie2
De Autoriteit Financiële Markten (AFM) heeft een werkwijze ontwikkeld voor de selectie van informele interventieinstrumenten. Deze werkwijze bestaat uit een gefaciliteerde sessie, software, een vragenlijst en een catalogus van instrumenten. Door al deze materialen vrij beschikbaar te maken en te delen met andere toezichthouders, willen wij een uitwisseling van methoden op gang brengen waarvan alle toezichthouders profiteren.

# Opties om de app te installeren
Er zijn veel manieren om de app in gebruik te nemen. Welke optie je kiest hangt af van de infrastructuur die je wilt gebruiken. De voornaamste keuzes zijn:

- **Linux of Windows.** Als je de app gebruikt op een Windows-machine, dan lijkt het erop dat de variabelen in seetings.cfg (zie onder) tussen aanhalingstekens moeten.
- **De broncode direct uitvoeren, of in een Docker container** Het grootste deel van deze handleiding gaat over de installatie op een webserver, maar het is ook mogeijk om de app direct te draaien.
```git clone https://github.com/FilipVdBergh/interventie2.git```
Zorg daarna voor een goede settings.cfg (zie ook onder). Als je python hebt geïnstalleerd, dan kan je de app direct draaien. 
- **Met een databaseserver (MariaDB, MS SQL) of met een lokaal bestand (SQLite).** De eerste optie is om de app aan te sluiten op een databaseserver (zoals MSSQL of MariaDB). Het voordeel is dat je gebruik kan maken van alle gemakken van een databaseserver, zoals het maken van goede backups, en de interface met de tool phpMyAdmin. Het nadeel is dat je een extra service draait. De tweede optie is om alles met sqlite bij te houden in een enkel bestand dat als database dient. Dit is makkelijker in te stellen, maar zorg er wel voor dat het SQLite bestand buiten de Docker container staat! Dan blijft de database behouden na een update, en kan jeen backup maken van alle gegevens.

# Voorbeelinstallatie
De snelste manier is om de app te draaien is om hem binnen te halen op Windows, en de app te configureren met sqlite. De meeste gebruikers zullen de app draaien op een Linux webserver. In deze handleiding gaan we er daarom vanuit je de app draait op een Linux server. Installeer Linux op een machine, en installeer vervolgens Docker. Daarna kan je de volgende stappen volgen om de app te installeren als webserver. 

- Installeer een operating systeem met docker.
- Als je de app als secure webserver wilt draaien, installeer dan certificaten voor veilige verbindingen.
- Als je MariaDB wilt gebruiken: installeer MariaDB en phpMyAdmin. Creeer een database en een gebruiker met toegangsrechten.
- Download de app van github.
- Configureer settings.cfg.
- Check de dockerfile of je de app runt met of zonder certificaten.
- Bouw en run de app
- Maak extra bestanden voor eenvoudige updates en het vernieuwen van de certificaten.

## Verkrijgen van certificaten
Deze certificaten zijn nodig vor het tot stand brengen van een versleutelde (https) verbinding. We maken hier gebruik van Let's Encrypt. Deze certificaten zijn specifiek voor het webadres dat je gebruikt. In de code hieronder moet je daarom <url> vervangen door je eigen webadres.
```
apt-get install certbot
ufw allow 80
certbot certonly --standalone --preferred-challenges http -d <url>
ufw allow 443
```

## Maak docker network
Dit netwerk wordt gebruik voor communicatie met de app.
```docker network create -d bridge my-network```

# Binnenhalen van de app
```git clone https://github.com/FilipVdBergh/interventie2.git```

## Pas de dockerfile aan
Er zijn een paar manieren om de app op te starten, en die hangen af van of er certificaten worden gebruikt. Open de dockerfile en (un)comment de juiste regels onderin het bestand.

## settings.cfg kopieren
Maak eerst een kopie van het settings.cfg bestand dat je zojuist hebt binnengehaald vanuit github, en zet het één directoryniveau hoger:
```mv interventie2/settings.cfg .```

# Stappen bij het gebruik van een databaseserver
Als je een databaseserver wilt gebruiken doorloop je deze extra stapppen. Als je de app gaat draaien in Azure zal je ook een databaseserver gebruiken, maar de Azure admin zal dan onderstaande stappen moeten doorlopen en toegang geven tot de database vanaf de app. Onderstaande stappen gelden voor een standalone server.

## Installeren van MariaDB:
```docker run --name mariadb -e MYSQL_ROOT_PASSWORD=<your-root-password> --network my_network -d mariadb:latest```

## Installeren van phpMyAdmin
```docker run --name phpmyadmin -d --network my_network --link mariadb:db -p 8081:80 phpmyadmin```

## Maak een nieuwe database aan op de server, maak een nieuwe gebruiker, en geef die toegang tot de database
Ga naar <ip-address>:8081
Create new database:    interventie2
Username:               interventie2_user
Password:               <your-user-password>
Geef de gemaakte gebruiker toegang tot de nieuwe database. Je kan phpMyAdmin stoppen als je dit hebt gedaan.
`docker stop phpmyadmin`

## settings.cfg aanpassen voor gebruik van een databaseserver
```
SECRET_KEY=SECRETKEY
APP_NAME=interventie2
ALLOW_DB_INIT=True
ALLOW_CATALOG_VIEW=False
ALLOW_CONTACT=False
ALLOW_SELF_REGISTRATION=True
MAINTAINER=interventieteam
MAINTAINER_EMAIL=interventie@afm.nl
SQLALCHEMY_DATABASE_URI=mysql://interventie2_user:<your-user-password>@mariadb:3306/interventie2
```

## Bouw en run de app
Vervang `<url>` door je eigen domein.
```
docker build -t interventie2 .
docker run --name interventie2 --env-file /root/settings.cfg -p 443:443 --network my_network --link mariadb --mount type=bind,source=/etc/letsencrypt/live/<url>/fullchain.pem,target=/etc/letsencrypt/certificates/fullchain.pem --mount type=bind,source=/etc/letsencrypt/live/<url>/privkey.pem,target=/etc/letsencrypt/certificates/privkey.pem -d interventie2
```

# Stappen bij het gebruik van sqlite
Als je sqlite wilt gebruiken moet je er voor zorgen dat het databestand op de host servwer staat, zodat de database niet gewist wordt als je de container herstart. Daarvoor kopieren we een bestaande database naar een hogergelegen directoryniveau:
```cp interventie2/instande/interventie2.db /root```

## settings.cfg aanpassen voor gebruik van sqlite
```
SECRET_KEY=SECRETKEY
APP_NAME=interventie2
ALLOW_DB_INIT=True
ALLOW_CATALOG_VIEW=False
ALLOW_CONTACT=False
ALLOW_SELF_REGISTRATION=True
MAINTAINER=interventieteam
MAINTAINER_EMAIL=interventie@afm.nl
SQLALCHEMY_DATABASE_URI=sqlite:///interventie2.db
```

## Bouw en run de app
Vervang `<url>` door je eigen domein.
```
docker build -t interventie2 .
docker run --name interventie2 --env-file /root/settings.cfg -p 443:443 --network my_network --mount type=bind,source=/root/interventie2.db,target=/app/instance/interventie2.db --mount type=bind,source=/etc/letsencrypt/live/<url>>/fullchain.pem,target=/etc/letsencrypt/certificates/fullchain.pem --mount type=bind,source=/etc/letsencrypt/live/<url>/privkey.pem,target=/etc/letsencrypt/certificates/privkey.pem -d interventie2
```

# Eerste gebruik van de app
Ga naar <url>/admin/initialize. Dit zorgt ervoor dat de gehele database wordt gemaakt.
- Login:             root:root
  
Verander het root wachtwoord direct, en maak een nieuwe gebruiker aan waarvanuit je voortaan werkt.

# Onderhoud
Onm de app eenvoudig te updaten kan je onderstaand bash-script gebruiken. Vervang `<url>` door je eigen domein.
```
docker stop interventie2
docker rm interventie2
rm -rf interventie2
git clone https://github.com/FilipVdBergh/interventie2.git
cd interventie2
docker build -t interventie2 .
docker run --name interventie2 --env-file /root/settings.cfg -p 443:443 --network my_network --link mariadb --mount type=bind,source=/etc/letsencrypt/live/<url>/fullchain.pem,target=/etc/letsencrypt/certificates/fullchain.pem --mount type=bind,source=/etc/letsencrypt/live/<url>/privkey.pem,target=/etc/letsencrypt/certificates/privkey.pem -d interventie2
```
