from models import db, Cliente, Prodotto, Fattura, VoceFattura, FatturaSequence, User
from dateutil.parser import parse
from datetime import datetime

class Form(object):
  errors = None
  
  def __init__(self, f):    # f=request.form  
	self.form = f
	self.errors = dict()
	
  def valido(self):
	return len(self.errors.keys())==0

class Params(object):
  def __init__(self, a):    # a=request.args
	self.args = a
	self.errors = dict()
	
  def valido(self):
	return len(self.errors.keys())==0

class FormNuovaFattura(Form):
  n_scontr1 = 0
  n_scontr2 = 0
  n_scontr3 = 0
  dtfatt=None
  numfatt=0
  
  def valido(self):
	self.numfatt=self.form['nfatt']
	
	try:
	  self.dtfatt=parse(str(self.form['dtfatt']))
	except:
	  self.errors['dtfatt'] = 'data non valida'
	  
	try:
	  self.n_scontr1 = int(self.form['scontr1'])
	except:
	  self.errors['scontr1'] = 'scontrino 1 non valido'
	  
	if(self.form['scontr2'] != ''):
	  try:
		self.n_scontr2 = int(self.form['scontr2'])
	  except:
		self.errors['scontr2'] = 'scontrino 2 non valido'
		 
	if(self.form['scontr3'] != ''):
	  try:
		self.n_scontr3 = int(self.form['scontr3'])
	  except:
		self.errors['scontr3'] = 'scontrino 3 non valido'
	
	return len(self.errors.keys())==0

#class ParamsAggiungiVoce(Params):
  #qta = 0
  #codart = ''
  #descr = ''
  #aliq = 22
  #prz = 0.00
  #idx_voce=0
  
  #def valido(self):
	#try:
	  #self.qta=int(self.args.get('qta'))
	  #if(self.qta == 0):
		#self.errors['qta'] = "quantita' non valida"	  
	#except:
	  #self.errors['qta'] = "quantita' non valida"
	  
	#self.descr = self.args.get('descr')
	
	#if(self.descr == ''):
	  #self.errors['descr'] = "descrizione non valida"
	
	#self.codart = self.args.get('codart')
	
	#try:
	  #self.aliq = int(self.args.get('aliq'))
	#except:
	  #self.errors['aliq'] = "aliquota mancante"
	
	#try:
	  #self.prz=float(self.args.get('prz'))
	#except:
	  #self.errors['prz'] = "prezzo mancante"
	
	#self.idx_voce=int(self.args.get('idx_voce'))
	
	#return len(self.errors.keys())==0

class FormProfilo(Form):
	user_id=0
	username=""
	nome=""
	email=""
	nuova_pwd=""
	conferma_pwd=""
	password_cambiata = False
	
	def __init__(self, f):    # f=request.form  
		self.errors = dict()
		self.user_id = f.get('id', 0)
		self.username = f.get('username')
		self.nome = f.get('nome')
		self.email = f.get('email')
		self.password = f.get('password')
		self.nuova_pwd = f.get('nuovapwd')
		self.conferma_pwd = f.get('confpwd')
		
	def autentica(self):
		u=db.session.query(User).get(self.user_id)
		return u.password == self.password
	
	def valido(self):
		if self.username.strip() == '':
			self.errors['username'] = "manca il nome utente"
			
		if self.nome.strip() == '':
			self.errors['nome'] = "manca il nome"
			
		if self.email.strip() == '':
			self.errors['email'] = "manca l'email"
			
		if self.nuova_pwd != '':
			# auth
			if self.autentica():
				if self.conferma_pwd == self.nuova_pwd:
					self.password_cambiata = True
				else:
					self.errors['nuovapwd'] = "le password non coincidono"
			else:
				self.errors['password'] = "password non corretta"
				
		return len(self.errors.keys())==0
			

class FormAggiungiVoce(FormNuovaFattura):
  qta = 0
  codart = ''
  descr = ''
  aliq = 22
  prz = 0.00
  idfatt = 0
  idx_voce=0
   
  def pulisci(self):
	self.qta=0
	self.codart=''
	self.descr=''
	self.aliq=22
	self.prz=0.00
	self.idfatt=0
	self.idx_voce=0
	  
  def valido(self):
	
	try:
	  self.idfatt=int(self.form['idfatt'])
	except:  
	  self.idfatt=0
	
	try:
	  self.qta=int(self.form['qta'])
	  if(self.qta == 0):
		self.errors['qta'] = "quantita' non valida"	  
	except:
	  self.errors['qta'] = "quantita' non valida"
	  
	self.descr = self.form['descr']
	
	if(self.descr == ''):
	  self.errors['descr'] = "descrizione non valida"
	
	self.codart = self.form['codart']
	
	try:
	  self.aliq = int(self.form['aliq'])
	except:
	  self.errors['aliq'] = "aliquota mancante"
	
	try:
	  self.prz=float(self.form['prz'])
	except:
	  self.errors['prz'] = "prezzo mancante"
	
	self.idx_voce=int(self.form['idx_voce'])
	
	super_valid=super(FormAggiungiVoce, self).valido()
	
	return super_valid and len(self.errors.keys())==0

class FormProdotto(object):
	id=0
	codice=""
	descrizione=""
	aliq=22
	prezzo=""
	
	def __init__(self, f):    # f=request.form  
		self.errors = dict()
		self.id = f.get('id', 0)
		self.codice = f.get('codice')
		self.descrizione = f.get('descrizione')
		self.aliquota = f.get('aliquota')
		self.prezzo = f.get('prezzo')
		
	def valido(self):
		# if(self.codice == ''):
			# self.errors['codice'] = "manca il codice"
		
		if(self.descrizione == ''):
			self.errors['descrizione'] = "manca la descrizione"
		
		if(self.aliquota == ''):
			self.errors['aliquota'] = "manca l'aliquota IVA"
		
		try:
			float(self.aliquota)
		except:
			self.errors['aliquota'] = "aliquota IVA non valida"
			
		if(self.prezzo == ''):
			self.errors['prezzo'] = "manca il prezzo"
		
		try:
			float(self.prezzo)
		except:
			self.errors['prezzo'] = "prezzo non valido"
			
		return len(self.errors.keys())==0
	
class FormCliente(object):
	ragsoc=""
	indirizzo=""
	cap=""
	citta=""
	piva=""
	cfisc=""
	telefono=""
	email=""
	
	def __init__(self, f):    # f=request.form  
		self.errors = dict()
		self.ragsoc = f.get('ragione_sociale')
		self.indirizzo = f.get('indirizzo')
		self.cap = f.get('cap')
		self.citta = f.get('citta')
		self.piva = f.get('p_iva')
		self.cap = f.get('cap')
		self.cfisc = f.get('cod_fiscale')
		self.telefono = f.get('telefono')
		self.email = f.get('email')

	def valido(self):
		if(self.ragsoc == ''):
			self.errors['ragsoc'] = "manca la ragione sociale"

		if(self.indirizzo == ''):
			self.errors['indirizzo'] = "manca l'indirizzo"

		if(self.cap == ''):
			self.errors['cap'] = "manca il cap"

		if(self.citta == ''):
			self.errors['citta'] = "manca la citt&agrave;"

		if(self.piva == ''):
			self.errors['piva'] = "manca la partita iva"

		if(self.cfisc == ''):
			self.errors['cfisc'] = "manca il codice fiscale"			

		if(self.telefono == ''):
			self.errors['telefono'] = "manca il telefono"

		if(self.email == ''):
			self.errors['email'] = "manca l'email"			

		return len(self.errors.keys())==0
		
class FormDate(Form):
	data_inizio=None
	data_fine=None
	
	def __init__(self, f):    # f=request.form  
		self.errors = dict()
		self.data_inizio=f.get('data_inizio')
		self.data_fine=f.get('data_fine')
		
	def valido(self):
		try:
			self.data_inizio=parse(str(self.data_inizio))
		except:
			self.errors['data_inizio'] = 'data non valida'
		
		try:
			self.data_fine=parse(str(self.data_fine))
		except:
			self.errors['data_fine'] = 'data non valida'
			
		return len(self.errors.keys())==0
		
class FormDateFatture(FormDate):
	nro_da=0
	nro_a=0
	anno=0
	
	def __init__(self, f):    # f=request.form  
		super(FormDateFatture, self).__init__(f)
		nro_da=f.get('nro_da', '')
		nro_a=f.get('nro_a', '')
		anno=f.get('anno', '')
		
		self.nro_da=0 if nro_da == '' else int(nro_da)
		self.nro_a=0 if nro_a == '' else int(nro_a)
		self.anno=0 if anno == '' else int(anno)
	
	def valido(self):
		return super(FormDateFatture, self).valido()