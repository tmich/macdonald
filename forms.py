from models import db, Cliente, Prodotto, Fattura, VoceFattura, FatturaTemp, VoceFatturaTemp, FatturaSequence

class Form:
  errors = None
  
  def __init__(self, f):	# f=request.form  
    self.form = f
    self.errors = dict()
    
  def valido(self):
    return len(self.errors.keys())==0


class FormNuovaFattura(Form):
  n_scontr1 = 0
  n_scontr2 = 0
  n_scontr3 = 0

  def valido(self):
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


class FormAggiungiVoce(Form):
  qta = 1
  codart = ''
  descr = ''
  aliq = 22
  prz = 0.00
  
  def pulisci(self):
    self.qta=1
    self.codart=''
    self.descr=''
    self.aliq=22
    self.prz=0.00
  
  def valido(self):
    try:
      self.qta=int(self.form['qta'])
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
    
    return len(self.errors.keys())==0
      