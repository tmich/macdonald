from models import db, Cliente, Prodotto, Fattura, VoceFattura, FatturaSequence
from dateutil.parser import parse

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