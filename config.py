#config.py

class Config(object):
  DEBUG = False
  SECRET_KEY = 'u,fdP%6;[T$nXDd)qhpVM-TyQ,yZu8#]u:eYd~~eu7g`5tf'
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  MAIL_SERVER = 'smtp.libero.it'
  MAIL_PORT=587
  MAIL_USE_SSL=False
  MAIL_USE_TLS=True
  MAIL_DEFAULT_SENDER=('Cartoleria Macdonald', 'aldomd@inwind.it')
  MAIL_USERNAME = 'aldomd@inwind.it'
  MAIL_PASSWORD = 'ALDOMAC03'
  BABEL_DEFAULT_LOCALE = 'it'
  
class ProductionConfig(Config):
  pass

class DevelopmentConfig(Config):
  DEBUG = True
  SQLALCHEMY_DATABASE_URI = 'mysql://aldo:aldo.2017@localhost/macdonald'
  #MYSQL_USER = 'aldo'
  #MYSQL_PASSWORD = 'aldo.2017'
  #MYSQL_DB = 'macdonald'
  #MYSQL_HOST = 'localhost'
