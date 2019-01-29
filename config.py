# config.py
# Questo file e' *DIVERSO* in sviluppo e produzione e non va messo in git!
#

class Config(object):
	DEVELOPMENT = False
	DEBUG = False
	SECRET_KEY = 'u,fdP%6;[T$nXDd)qhpVM-TyQ,yZu8#]u:eYd~~eu7g`5tf'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	BABEL_DEFAULT_LOCALE = 'it'
	SERVIZIO_AGYO = "5.249.149.66"
	PORTA_AGYO = "18861"


class ProductionConfig(Config):
	pass


class DevelopmentConfig(Config):
	DEVELOPMENT = True
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'mysql://aldo:aldo.2017@localhost/macdonald'
	
	
def get_config_name():
	return 'config.DevelopmentConfig'