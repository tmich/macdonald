from __future__ import print_function
import os, config, json, datetime, flask, sys
from functools import wraps
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response
from flask_mail import Mail, Message
from flask.json import JSONEncoder, JSONDecoder
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal
from pdfs import create_pdf
from models import db, Anagrafica, Cliente, Prodotto, Fattura, VoceFattura, InvioFattura, User, FatturaTemp, VoceFatturaTemp, FatturaSequence

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
app.static_folder = 'static' 
mail_ext = Mail(app)
#db = SQLAlchemy(app)
db.init_app(app)

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
  p = Prodotto.query.get(id)
  return render_template('prodotto.html', prodotto=p)
  
@app.route('/nuovo_prodotto', methods=['GET', 'POST'])
@login_required
def nuovo_prodotto():
  return render_template('prodotto.html', prodotto=None)

@app.route('/salva_prodotto', methods=['POST'])
@login_required
def salva_prodotto():
  if request.method == 'POST':
	f = request.form
	id = f['id']
	p = Prodotto.query.get(id)
	p.codice = f['codice']
	p.descr = f['descrizione']
	p.aliq = f['aliquota']
	p.prezzo = f['prezzo']
	
	db.session.commit()
	flash('Articolo aggiornato')
  return redirect(url_for('prodotti', page=0))
	
@app.route('/profilo', methods=['GET', 'POST'])
@login_required
def profilo():
  if request.method == 'POST':
	f = request.form
	u = User.query.get(g.user.id)
	u.nome = f['nome']
	u.email = f['email']
	db.session.commit()
	flash('Profilo utente aggiornato')
  return render_template('profilo.html')
  
@app.route('/fatture_cliente/<int:id>/<int:page>')
@login_required
def fatture_cliente(id, page=0):
  pagenum = 20
  offset = page * pagenum
  cli = Cliente.query.get(id)
  fatture = Fattura.query.filter_by(cliente_id=id).order_by('data desc').offset(offset).limit(pagenum)
  return render_template('fatture_cliente.html', fatture=fatture, cliente=cli, page=page, cnt=fatture.count())

@app.route('/prodotti.json', methods=['GET','POST'])
def articoli_json():
  articoli = Prodotto.query.all()
  return json.dumps([a.to_json() for a in articoli])

#@login_required
#@app.route('/nfattura/<int:idc>/delvoce/<int:idv>', methods=['GET'])
#def rimuovi_voce_temp(idc, idv):
  #v=db.session.query(VoceFatturaTemp).get(idv).first()
  #if(v!=None):
    #db.session.delete(v)
    #db.session.commit()
    #redirect(url_for(nfattura, idc=idc))


@login_required
@app.route('/nfattura/<int:idc>', methods=['GET', 'POST'])
def nuova_fattura(idc):     
  cli=Cliente.query.get(idc)
  dt=datetime.date.today()
  seq=FatturaSequence()
  numfatt=seq.next_val(dt.year)
  fatt=Fattura(cli, dt, numfatt)
  db.session.add(fatt)
  db.session.commit()
    
  return redirect(url_for('mod_fattura', idfatt=fatt.id))

@login_required
@app.route('/invio', methods=['GET'])
def fatture_da_inviare():
  fatture_da_inviare=db.session.query(InvioFattura).filter_by(data_invio=None).all()
  return render_template('fatture_da_inviare.html', fatture_da_inviare=fatture_da_inviare, cnt=len(fatture_da_inviare))

@login_required
@app.route('/invia_tutte', methods=['GET'])
def invia_tutte():
  fatture_da_inviare=db.session.query(InvioFattura).filter_by(data_invio=None).all()
  min_righe=10
  dest = request.args.get('next')
  
  for inv in fatture_da_inviare:
    subject = "Fattura n. %d" % inv.fattura.num
    recipient = inv.fattura.cliente.email
    mail_to_be_sent = Message(subject=subject, recipients=[recipient])
    mail_to_be_sent.body = "In allegato la fattura. Saluti."  
    n_righe = max(len(inv.fattura.voci), min_righe) - min(len(inv.fattura.voci), min_righe)
    pdf=create_pdf(render_template('pdf.html', fattura=inv.fattura, n_righe=n_righe))
    mail_to_be_sent.attach("Fattura.pdf", "application/pdf", pdf.getvalue())
    try:
      mail_ext.send(mail_to_be_sent)
      inv.data_invio=datetime.datetime.now
      db.session.commit()
    except:
      flash('Si &egrave; verificato un errore')
      return redirect(dest)
    
   
  flash('Invio effettuato con successo')
  return redirect(dest)
    

@login_required
@app.route('/invio_fatt/<int:idfatt>', methods=['GET'])
def invia_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  invio_fatt=InvioFattura(fatt, fatt.cliente.email)
  db.session.add(invio_fatt)
  db.session.commit()
  flash('Invio fattura prenotato con successo')
  dest = request.args.get('next')
  return redirect(dest)

@login_required
@app.route('/dfattura/<int:idfatt>', methods=['GET'])
def del_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  db.session.delete(fatt)
  db.session.commit()
  dest = request.args.get('next')
  return redirect(dest)

@app.route('/stampa_fatt/<int:idfatt>', methods=['GET'])
def stampa_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  min_righe=10
  n_righe = max(len(fatt.voci), min_righe) - min(len(fatt.voci), min_righe)

  pdf=create_pdf(render_template('pdf.html', fattura=fatt, n_righe=n_righe))
  response=make_response(pdf.getvalue())
  response.headers['Content-Type'] = 'application/pdf'
  response.headers['Content-Disposition'] = 'attachment; filename=fattura.pdf'
  return response
  
@login_required
@app.route('/mfattura/<int:idfatt>', methods=['GET','POST'])
def mod_fattura(idfatt):
  voce_da_modificare=None
  fatt = db.session.query(Fattura).get(idfatt)
  errors=dict()
  codart=None
  descr=None
  qta=None
  prz=None
  aliq=None
  if(fatt==None):
    abort(404)
      
  #if(request.method == 'GET'):
  if('oper' in request.args):
    id_voce = request.args.get('id_voce')
    v = db.session.query(VoceFattura).get(id_voce)
    oper = request.args.get('oper')
    if(oper=='del'):	# elimina voce
      db.session.delete(v)
      db.session.commit()
      return redirect(url_for('mod_fattura', idfatt=fatt.id))
    else:
      voce_da_modificare=v
      codart=voce_da_modificare.codart
      descr=voce_da_modificare.descr
      qta=voce_da_modificare.qta
      prz=voce_da_modificare.prezzo
      aliq=voce_da_modificare.aliq
	
  if(request.method == 'POST'):  
    f=request.form
    
    scontr1=f['scontr1']
    scontr2=f['scontr2']
    scontr3=f['scontr3']
    qta=f['qta']
    descr=f['descr']
    prz=f['prz']
    aliq=f['aliq']
    codart=f['codart']
    
    try:
      scontr1=int(scontr1)
    except:
      errors['scontr1'] = 'scontrino 1 non valido'
      
    if(scontr2 != ''):
      try:
	scontr2=int(scontr2)
      except:
	errors['scontr2'] = 'scontrino 2 non valido'
    
    if(scontr3 != ''):
      try:
	scontr3=int(scontr3)
      except:
	errors['scontr3'] = 'scontrino 3 non valido'
      
    try:
      qta=int(qta)
    except:
      errors['qta'] = 'quantit&agrave; non valida'
      
    if(descr.strip()==''):
      errors['descr'] = 'descrizione mancante'
    
    try:
      prz = float(prz)
      if(prz==0):
	raise Exception("")
    except:
      errors['prz']='prezzo non valido'
    
    try:
      aliq = float(aliq)
      if(aliq==0):
	raise Exception("")
    except:
      errors['aliq']='aliquota IVA non valida'
    
    print(errors, file=sys.stderr)
    
    if(len(errors.keys())==0):
      fatt.n_scontr1 = scontr1
      fatt.n_scontr2 = scontr2
      fatt.n_scontr3 = scontr3
      
      if('vmod' in f):	# modifica voce
	v=db.session.query(VoceFattura).get(f['vmod'])
	v.codart=codart
	v.descr=descr
	v.qta=qta
	v.prezzo=prz
	v.aliq=aliq
      else:	 # crea voce
	v=fatt.crea_voce(codart=codart,descr=descr,qta=qta,prezzo=prz,aliq=aliq)
	fatt.voci.append(v)
      
      db.session.add(v)
      db.session.commit()
      return redirect(url_for('mod_fattura', idfatt=idfatt))

      #print("\t tot. imp. voce: %.2f" % v.tot_imponibile(), file=sys.stderr)
      #print("\t tot. imp. fattura: %.2f" % fatt.tot_imponibile(), file=sys.stderr)
  
  return render_template('fattura.html',fattura=fatt,vmod=voce_da_modificare,codart=codart,descr=descr,qta=qta,
			 prz=prz,aliq=aliq,errors=errors)

@app.route('/dett_fattura/<int:id>')
@login_required
def dett_fattura(id, page=0):
  pagenum = 20
  offset = page * pagenum
  f = Fattura.query.get(id)
  return render_template('dett_fattura.html', fattura=f, voci=f.voci, tot=f.totale())



if __name__ == "__main__":
  #app.run(host='93.186.254.106', port=80)
  app.run()