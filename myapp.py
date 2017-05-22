import os, config, json
from functools import wraps
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
app.static_folder = 'static' 
db = SQLAlchemy(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

## Views

@app.before_request
def load_user():
  if "uid" in session:
    g.user = User.query.get(session['uid'])
  else:
    g.user = None #{'id' : 0, 'nome': 'Guest'}  # Make it better, use an anonymous User instead

@app.route("/")
def main():
  return render_template('index.html', utente=g.user)

@app.route('/login', methods=['GET', 'POST'])
def login():
  error = "Per accedere alla risorsa richiesta e' necessaria l'autenticazione"
  
  if request.method == 'POST':
    usr = str(request.form['username'])
    pwd = str(request.form['password'])
    u = User.query.filter_by(username=usr).first()
    if u != None:
      if u.password == pwd:
	g.user = u
	session['logged_in'] = True
	session['uid'] = u.id
	return redirect(url_for('main'))
      else:
	error = 'Nome utente o password errati'
  return render_template('login.html', error=error)

@app.route('/logout')
def logout():
  g.user = None
  session['logged_in'] = False
  if 'uid' in session:
    session.pop('uid')
  return redirect(url_for('main'))

@app.route('/clienti', methods=['GET'])
@app.route('/clienti/<int:page>')
@login_required
def clienti(page=0):
  pagenum = 20
  offset = page * pagenum
  clienti = Cliente.query.order_by('ragsoc').offset(offset).limit(pagenum)
  return render_template('clienti.html', clienti=clienti, page=page, utente=g.user)

@app.route('/cerca_cliente', methods=['POST'])
@login_required
def cerca_cliente(page=0):
  if request.method == 'POST':
    f = request.form
    q = str(f['query'])
    pagenum = 20
    #offset = page * pagenum
    offset=0
    clienti = db.session.query(Cliente).filter(Cliente.ragsoc.like('%'+q+'%')).order_by('ragsoc').offset(offset).limit(pagenum)
    return render_template('clienti.html', clienti=clienti, page=page, utente=g.user)

@app.route('/salva_cliente', methods=['POST'])
@login_required
def salva_cliente():
  if request.method == 'POST':
    f = request.form
    ragsoc = str(f['ragione_sociale'])
    ind = str(f['indirizzo'])
    cap = f['cap']
    citta = str(f['citta'])
    p_iva = str(f['p_iva'])
    cfisc = str(f['cod_fiscale'])
    tel = str(f['telefono'])
    email = str(f['email'])
    id = f['id']
    cli = Cliente.query.get(id)
    cli.ragsoc = ragsoc
    cli.indirizzo = ind
    cli.p_iva = p_iva
    cli.cod_fisc = cfisc
    cli.indirizzo = ind
    cli.citta = citta
    cli.cap = cap
    cli.prov = None
    cli.tel = tel
    cli.fax = None
    cli.email = email
    
    db.session.commit()
    flash('Anagrafica cliente aggiornata')
    
    return redirect(url_for('clienti'))

@app.route('/nuovo_cliente', methods=['GET', 'POST'])
@login_required
def nuovo_cliente():
  if request.method == 'POST':
    f = request.form
    cli = Cliente()
    cli.ragsoc = str(f['ragione_sociale'])
    cli.indirizzo = str(f['indirizzo'])
    cli.cap = f['cap']
    cli.citta = str(f['citta'])
    cli.p_iva = str(f['p_iva'])
    cli.cod_fisc = str(f['cod_fiscale'])
    cli.tel = str(f['telefono'])
    cli.email = str(f['email'])
    
    db.session.add(cli)
    db.session.commit()
    flash('Anagrafica cliente creata')
    return redirect(url_for('clienti'))    
  return render_template('cliente.html', cliente=None, utente=g.user)

@app.route('/cliente/<int:id>')
@login_required
def cliente(id):
    cli = Cliente.query.get(id)
    return render_template('cliente.html', cliente=cli, utente=g.user)

@app.route('/prodotti', methods=['GET'])
@app.route('/prodotti/<int:page>')
@login_required
def prodotti(page=0):
  pagenum = 20
  offset = page * pagenum
  prodotti = Prodotto.query.order_by('descr').offset(offset).limit(pagenum)
  return render_template('prodotti.html', prodotti=prodotti, page=page, utente=g.user)

@app.route('/prodotto/<int:id>')
@login_required
def prodotto(id):
  return id

### Models

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
  tel = db.Column(db.String(20))
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

  def __init__(self):
    canc = 0
    
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
  canc = db.Column(db.Integer)
  
  def __init__(self, cliente, data, n_scontr1):
    self.cliente = cliente
    self.data = data
    self.n_scontr1 = n_scontr1
    self.canc = 0

class VoceFattura(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  seq = db.Column(db.Integer)
  codart = db.Column(db.String(80))
  descr = db.Column(db.String(120))
  qta = db.Column(db.Integer)
  prezzo = db.Column(db.Numeric(10, 2)) 
  aliq = db.Column(db.Integer)
  fattura_id = db.Column(db.Integer, db.ForeignKey('fattura.id'))
  fattura = db.relationship('Fattura',
			    backref=db.backref('voci', lazy='dynamic'))
  canc = db.Column(db.Integer)
  
  def __init__(self):
    self.canc = 0
    
  def __repr__(self):
    return '%d x %r' % (self.qta, self.descr)
    
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

  def __repr__(self):
      return '<User %r>' % self.username
    

if __name__ == "__main__":
  app.run()