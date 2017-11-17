## models.py
from __future__ import print_function
from flask_sqlalchemy import SQLAlchemy
import sys, datetime
from decimal import Decimal
from flask.json import jsonify

db = SQLAlchemy()

class Anagrafica(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  ragsoc = db.Column(db.String(120))
  descr = db.Column(db.String(120))
  p_iva = db.Column(db.String(20))
  cod_fisc = db.Column(db.String(20))
  indirizzo = db.Column(db.String(120))
  citta = db.Column(db.String(120))
  cap = db.Column(db.String(10))
  prov = db.Column(db.String(2))
  tel = db.Column(db.String(20))
  mf = db.Column(db.String(20))
  fax = db.Column(db.String(20))
  email = db.Column(db.String(120))

class Cliente(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  old_cod = db.Column(db.Integer)
  ragsoc = db.Column(db.String(120))
  p_iva = db.Column(db.String(20))
  cod_fisc = db.Column(db.String(20))
  indirizzo = db.Column(db.String(120))
  citta = db.Column(db.String(120))
  cap = db.Column(db.String(10))
  prov = db.Column(db.String(2))
  tel = db.Column(db.String(50))
  fax = db.Column(db.String(20))
  email = db.Column(db.String(120))
  canc = db.Column(db.Integer)
  
  def __init__(self):
	canc = 0
  
class Prodotto(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  codice = db.Column(db.String(80))
  descr = db.Column(db.String(120))
  aliq = db.Column(db.Integer)
  prezzo = db.Column(db.Numeric(10, 2))
  canc = db.Column(db.Integer)

  def to_json(self):
	data = {'artid'  : self.id,
	    'codice' : self.codice,
	    'descr'  : self.descr,
	    'aliq'   : self.aliq,
	    'prezzo' : str(self.prezzo)}
	return data

  def __init__(self):
	self.canc = 0
	
class Fattura(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  num = db.Column(db.Integer)
  data = db.Column(db.Date)
  n_scontr1 = db.Column(db.Integer)
  n_scontr2 = db.Column(db.Integer)
  n_scontr3 = db.Column(db.Integer)
  cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
  cliente = db.relationship('Cliente',
			    backref = db.backref('fatture', lazy='dynamic'))
  voci = db.relationship('VoceFattura', cascade="save-update, merge, delete")
  canc = db.Column(db.Integer)
  stampato = db.Column(db.Integer)	## ALTER TABLE `fattura` ADD COLUMN `stampato` INT NOT NULL DEFAULT '0' AFTER `canc`;
  
  def __init__(self, cliente, data, num = 0):
	self.cliente = cliente
	self.data = data
	self.num = num
	self.canc = 0
	self.stampato = 0
	self.n_scontr1 = 0
	self.n_scontr2 = 0
	self.n_scontr3 = 0
	
  @property
  def scontrini(self):
	lst = [self.n_scontr1]
	if self.n_scontr2 !=0:
	  lst.append(self.n_scontr2)
	if self.n_scontr3 !=0:
	  lst.append(self.n_scontr3)
	return '-'.join(str(x) for x in lst)

  def n_scontrini(self):
	n=0
	for x in [self.n_scontr1, self.n_scontr2, self.n_scontr3]:
	  if x != 0:
	    n=n+1
	return n
	
  def imponibile(self):
	return sum([v.imponibile() for v in self.voci])

  def iva(self):
	return sum([v.iva() for v in self.voci])

  def totale(self):
	return sum([v.totale() for v in self.voci])

  def crea_voce(self, codart, descr, qta, prezzo, aliq):
	return VoceFattura(codart, descr, qta, prezzo, aliq)
	
  # def stampato(self):
	# return self.stampato==1

class VoceFattura(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  seq = db.Column(db.Integer)
  codart = db.Column(db.String(80))
  descr = db.Column(db.String(120))
  qta = db.Column(db.Integer)
  prezzo = db.Column(db.Numeric(10, 2)) 
  aliq = db.Column(db.Integer)
  fattura_id = db.Column(db.Integer, db.ForeignKey('fattura.id'))
  canc = db.Column(db.Integer)
	
  def __init__(self, codart, descr, qta, prezzo, aliq):
	self.codart=codart
	self.descr=descr
	self.qta=qta
	self.prezzo=prezzo
	self.aliq=aliq
	self.canc = 0
  
  def iva(self):
	p = self.prezzo * self.qta
	iva = Decimal(p) - Decimal(self.imponibile())
	return round(iva, 2)
  
  def prezzo_unitario(self):
	p = Decimal(self.prezzo)
	return round(p, 2)
  
  def imponibile(self):
	p = self.prezzo * self.qta
	al = Decimal(round(self.aliq, 2))
	cnv = Decimal(al/100)+1
	imponibile = Decimal(p / cnv, 2)
	#print("Imponibile: " ,file=sys.stderr)
	#print(round(imponibile, 2),file=sys.stderr)
	return round(imponibile, 2)
  
  def totale(self):
	tot=self.iva()+self.imponibile()
	return tot

class InvioFattura(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  fattura_id = db.Column(db.Integer, db.ForeignKey('fattura.id'))
  data_invio=db.Column(db.Date)
  email=db.Column(db.String(120))
  esito=db.Column(db.String(2)) 	#'OK', 'KO'
  errore=db.Column(db.String(200))
  fattura = db.relationship('Fattura',
			    backref = db.backref('invii', lazy='dynamic'))
  
  def __init__ (self, fattura, email):
	self.fattura_id=fattura.id
	self.email=email


class ListaDistribuzione(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  nome = db.Column(db.String(120))
  data_creazione = db.Column(db.DateTime, default=datetime.datetime.utcnow) 
  canc = db.Column(db.Integer, default=0)
  membri = db.relationship('MembroListaDistribuzione', cascade="save-update, merge, delete")


class MembroListaDistribuzione(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
  cliente = db.relationship('Cliente',
			    backref = db.backref('membro', lazy='dynamic'))
  lista_id = db.Column(db.Integer, db.ForeignKey('lista_distribuzione.id'))
  email = db.Column(db.String(120))
  canc = db.Column(db.Integer, default=0)
  
	
class EmailConfig(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80))
  password = db.Column(db.String(80))
  nome = db.Column(db.String(120))
  email = db.Column(db.String(120))
  server = db.Column(db.String(80))
  porta = db.Column(db.Integer)
  ssl = db.Column(db.Boolean)
  tls = db.Column(db.Boolean)
  attivo = db.Column(db.Boolean)
  
  def __init__(self, username, password, nome, server, email, porta, ssl=False, tls=True, attivo=True):
	self.username = username
	self.password = password
	self.nome = nome
	self.server = server
	self.email = email
	self.porta = porta
	self.ssl = ssl
	self.tls = tls
	self.attivo = attivo


class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True)
  password = db.Column(db.String(80))
  email = db.Column(db.String(120), unique=True)
  nome = db.Column(db.String(80))
  profilo = db.Column(db.String(1))
  attivo = db.Column(db.Integer)

  def __init__(self, username, password, email, nome, profilo='U', attivo=1):
	self.username = username
	self.password = password
	self.email = email
	self.nome = nome
	self.profilo = profilo
	self.attivo = attivo
	
  def is_admin(self):
	return self.profilo == 'A'

  def __repr__(self):
	  return '<User %r>' % self.username

class Messaggio(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nome = db.Column(db.String(80))
	testo = db.Column(db.String(2000))
	attivo = db.Column(db.Integer)
	predefinito = db.Column(db.Integer)
	
	def __init__(self, nome, testo, attivo=1, predefinito=0):
		self.id = 0
		self.nome = nome
		self.testo = testo
		self.attivo = attivo
		self.predefinito = predefinito
	  
class FatturaSequence():
  def next_val(self, year):
	num = 0
	qry = "select max(num) from fattura where year(data) = %d" % year;
	result = db.engine.execute(qry)
	for row in result:
	  num = row[0] + 1
	return num

# classi per la memorizzazione in sessione delle fatture

class ObjVoce:
  def __init__(self, qta, codart, descr, aliq, prz):
	self.qta=qta
	self.codart=codart
	self.descr=descr
	self.aliq=aliq
	self.prezzo=prz

  def iva(self):
	p = self.prezzo * self.qta
	iva = Decimal(p) - Decimal(self.imponibile())
	return round(iva, 2)

  def prezzo_unitario(self):
	p = Decimal(self.prezzo)
	return round(p, 2)
	
  def imponibile(self):
	p = Decimal(self.prezzo * self.qta)
	al = Decimal(round(self.aliq, 2))
	cnv = Decimal(al/100)+1
	imponibile = Decimal(p / cnv, 2)
	#print("Imponibile: " ,file=sys.stderr)
	#print(round(imponibile, 2),file=sys.stderr)
	return round(imponibile, 2)
  
  def totale(self):
	tot=self.iva()+self.imponibile()
	return tot

class ObjFatt:
  def __init__(self, num, n_scontr1, n_scontr2, n_scontr3, dt, id_cliente, id=0):
	self.num=num
	self.n_scontr1=n_scontr1
	self.n_scontr2=n_scontr2
	self.n_scontr3=n_scontr3
	self.dt=dt
	self.id_cliente=id_cliente
	self.voci = []
	self.id=id
	
  def aggiungi(self, voce):
	self.voci.append(voce)
	
  def rimuovi(self, idx):
	del self.voci[idx]
  
  def imponibile(self):
	return sum([v.imponibile() for v in self.voci])
  
  def iva(self):
	return sum([v.iva() for v in self.voci])

  def totale(self):
	return sum([v.totale() for v in self.voci])
	