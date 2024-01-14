from os import environ

class BaseConfig(object):
	SECRET_KEY = 'REPLACE_THIS_5DAFJ9E1B7GD4XH'
	APP_VERSION = '1.0'
	FILETYPE_VERSION = '1.0'
	DEBUG = False
	TESTING = False
	APP_NAME = environ.get('APP_NAME', 'interventie2')
	ALLOW_CATALOG_VIEW = environ.get('ALLOW_CATALOG_VIEW', False)
	ALLOW_DB_INIT = environ.get('ALLOW_DB_INIT', False)
	MAINTAINER = environ.get('MAINTAINER', 'interventieteam')
	MAINTAINER_EMAIL = environ.get('MAINTAINER_EMAIL', 'interventie@afm.nl')
	SQLALCHEMY_DATABASE_URI = environ.get('CONNECTION_STRING')

class DevelopmentConfig(BaseConfig):
	DEBUG = True
	TESTING = True
	
class TestingConfig(BaseConfig):
	DEBUG = False
	TESTING = True

class ProductionConfig(BaseConfig):
	SECRET_KEY = environ.get("$3V\V5U2*H~VX]):57DSS7M@J")