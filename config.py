#config.py

class Config(object):
  DEBUG = False
  
class ProductionConfig(Config):
  pass

class DevelopmentConfig(Config):
  DEBUG = True
  MYSQL_USER = 'aldo'
  MYSQL_PASSWORD = 'aldo.2017'
  MYSQL_DB = 'macdonald'
  MYSQL_HOST = 'localhost'
