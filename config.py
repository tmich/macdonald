#config.py

class Config(object):
  DEBUG = False
  SECRET_KEY = 'u,fdP%6;[T$nXDd)qhpVM-TyQ,yZu8#]u:eYd~~eu7g`5tf'
  
class ProductionConfig(Config):
  pass

class DevelopmentConfig(Config):
  DEBUG = True
  SQLALCHEMY_DATABASE_URI = 'mysql://aldo:aldo.2017@localhost/macdonald'
  #MYSQL_USER = 'aldo'
  #MYSQL_PASSWORD = 'aldo.2017'
  #MYSQL_DB = 'macdonald'
  #MYSQL_HOST = 'localhost'
