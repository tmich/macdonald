from __future__ import print_function
import os, config, json, datetime, flask, sys
from functools import wraps
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response, jsonify
from flask_mail import Mail, Message
from flask.json import JSONEncoder, JSONDecoder
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, format_datetime, format_date
from decimal import Decimal
from pdfs import create_pdf
from models import db, Anagrafica, Cliente, Prodotto, Fattura, VoceFattura, InvioFattura, User, FatturaSequence, ObjFatt, ObjVoce
from forms import FormNuovaFattura, FormAggiungiVoce, FormNuovaFattura
import jsonpickle
#from dateutil.parser import parse

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
app.static_folder = 'static' 
mail_ext = Mail(app)
#db = SQLAlchemy(app)
db.init_app(app)
babel = Babel(app)

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
  pagenum = 50
  offset = page * pagenum
  cnt = Cliente.query.count()
  last_page = cnt / pagenum
  clienti = Cliente.query.order_by('ragsoc').offset(offset).limit(pagenum)
  return render_template('clienti.html', clienti=clienti, page=page, cnt=cnt, last_page=last_page, utente=g.user)

@app.route('/cerca_cliente', methods=['POST'])
@login_required
def cerca_cliente(page=0):
  if request.method == 'POST':
    f = request.form
    q = str(f['query'])
    pagenum = 50
    #offset = page * pagenum
    offset=0
    clienti = db.session.query(Cliente).filter(Cliente.ragsoc.like('%'+q+'%')).order_by('ragsoc').offset(offset).limit(pagenum)
    cnt = clienti.count()
    last_page = cnt / pagenum
    return render_template('clienti.html', clienti=clienti, page=page, cnt=cnt, last_page=last_page, utente=g.user)

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
    flash('Anagrafica cliente aggiornata', 'success')
    
    return redirect(url_for('cliente', id=id))

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
def prodotti():
  prodotti = Prodotto.query.order_by('descr')
  return render_template('prodotti.html', prodotti=prodotti, utente=g.user)

@app.route('/prodotto/<int:id>')
@login_required
def prodotto(id):
  p = Prodotto.query.get(id)
  return render_template('prodotto.html', prodotto=p)
  
@app.route('/nuovo_prodotto')
@login_required
def nuovo_prodotto():
  return render_template('prodotto.html', prodotto=None)

@app.route('/salva_prodotto', methods=['POST'])
@login_required
def salva_prodotto():
  if request.method == 'POST':
    f = request.form

    if 'id' in f:
      id = f['id']
      p = Prodotto.query.get(id)
    else:
      p=Prodotto()
    
    p.codice = f['codice']
    p.descr = f['descrizione']
    p.aliq = f['aliquota']
    p.prezzo = f['prezzo']
    
    if not 'id' in f:
      db.session.add(p)
    
    db.session.commit()
    
    flash('Articolo aggiornato', 'success')
    
    return redirect(url_for('prodotto', id=p.id))
	
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
  pagenum = 50
  offset = page * pagenum
  cli = Cliente.query.get(id)
  cnt = Fattura.query.filter_by(cliente_id=id).count()
  last_page = cnt / pagenum
  fatture = Fattura.query.filter_by(cliente_id=id).order_by('data desc').offset(offset).limit(pagenum)
  return render_template('fatture_cliente.html', fatture=fatture, cliente=cli, page=page, cnt=cnt, last_page=last_page)

@app.route('/prodotti.json', methods=['GET','POST'])
def articoli_json():
  articoli = Prodotto.query.all()
  return json.dumps([a.to_json() for a in articoli])

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

#@login_required
#@app.route('/dfattura/<int:idfatt>', methods=['GET'])
#def del_fattura(idfatt):
  #fatt = db.session.query(Fattura).get(idfatt)
  #db.session.delete(fatt)
  #db.session.commit()
  #dest = request.args.get('next')
  #return redirect(dest)

@app.route('/stampa_fatt/<int:idfatt>', methods=['GET'])
def stampa_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  min_righe=10
  n_righe = max(len(fatt.voci), min_righe) - min(len(fatt.voci), min_righe)

  pdf=create_pdf(render_template('pdf.html', fattura=fatt, n_righe=n_righe))
  response=make_response(pdf.getvalue())
  response.headers['Content-Type'] = 'application/pdf'
  response.headers['Content-Disposition'] = 'inline; filename=fattura.pdf'
  return response

@login_required
@app.route('/vfattura/<int:idfatt>', methods=['GET'])
def vis_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  return render_template('vfattura.html',fattura=fatt)

@login_required
@app.route('/nuova_fattura/<int:id_cliente>', methods=['GET','POST'])
def nuova_fattura(id_cliente):
  errors=[]
  n_scontr1=0
  n_scontr2=0
  n_scontr3=0
  cli=db.session.query(Cliente).get(id_cliente)
  numfatt=FatturaSequence().next_val(datetime.date.today().year)
  session['fatt']=None
  session.pop('fatt')
  
  if request.method=='POST':
    f=FormNuovaFattura(request.form)
    errors=f.errors
    if(f.valido()):
      n_scontr1=f.n_scontr1
      n_scontr2=f.n_scontr2
      n_scontr3=f.n_scontr3
      dt=f.dtfatt
      numfatt=f.numfatt
      # creo l'oggetto ObjFatt da memorizzare in sessione
      fatt=ObjFatt(numfatt,n_scontr1,n_scontr2,n_scontr3,dt,id_cliente)
      fatt.id_cliente=id_cliente
      session['fatt']=jsonpickle.encode(fatt)
      return redirect(url_for('componi_fattura'))
	  
  return render_template('nuova_fattura.html', cliente=cli, datafattura=datetime.date.today(), numfattura=numfatt, errors=errors)

@login_required
@app.route('/modifica_fattura/<int:id>')
def modifica_fattura(id):
  session['fatt']=None
  session.pop('fatt')
  fattura=db.session.query(Fattura).get(id)
  
  # creo l'oggetto ObjFatt da memorizzare in sessione
  objf=ObjFatt(fattura.num,fattura.n_scontr1,fattura.n_scontr2,fattura.n_scontr3,fattura.data,fattura.cliente_id,id=fattura.id)
  for v in fattura.voci:
    objv=ObjVoce(qta=v.qta, codart=v.codart, descr=v.descr, aliq=v.aliq, prz=v.prezzo)
    objf.aggiungi(objv)
    
  session['fatt']=jsonpickle.encode(objf)
  return redirect(url_for('componi_fattura'))

@login_required
@app.route('/componi_fattura', methods=['GET','POST'])
def componi_fattura():
  if(not 'fatt' in session):
    abort(404)
    
  errors=[]
  fatt=jsonpickle.decode(session['fatt'])
  cli=db.session.query(Cliente).get(fatt.id_cliente)
  
  codart='' 
  descr='' 
  qta=0
  prezzo=0.0
  aliq=''
  idx_voce=0
  
  if(request.method=='GET'):
    if('idx' in request.args):
      idx_voce=request.args.get('idx')
      codart=request.args.get('codart')
      descr=request.args.get('descr')
      qta=request.args.get('qta')
      prezzo=request.args.get('prezzo')
      aliq=request.args.get('aliq')
  elif(request.method=='POST'):
    if('salva_fattura' in request.form):
      #salva fattura
      f = FormNuovaFattura(request.form)
      
      if(f.valido()):
	return salva_fattura(f)
      else:
	errors=f.errors
    else:
      # aggiungi voce
      f = FormAggiungiVoce(request.form)

      if(f.valido()):
	return aggiungi_voce(f)
      else:
	codart=f.codart
	prezzo=f.prz
	qta=f.qta
	descr=f.descr
	aliq=f.aliq
	errors=f.errors
      
  return render_template('componi_fattura.html',errors=errors,datafattura=fatt.dt,numfatt=fatt.num,n_scontr1=fatt.n_scontr1,n_scontr2=fatt.n_scontr2,n_scontr3=fatt.n_scontr3,cliente=cli,imponibile=fatt.imponibile(),iva=fatt.iva(),totale=fatt.totale(),voci=fatt.voci,codart=codart,descr=descr,qta=qta,prezzo=prezzo,aliq=aliq,idx_voce=idx_voce)  

def aggiungi_voce(f):
  objf=jsonpickle.decode(session['fatt'])
  cli=db.session.query(Cliente).get(objf.id_cliente)
  codart='' 
  descr='' 
  qta=0
  prezzo=0.0
  aliq=''
  idx_voce=0
  
  objv=ObjVoce(qta=f.qta,descr=f.descr,codart=f.codart,prz=f.prz,aliq=f.aliq)
  if(f.idx_voce > 0):
    ## sostituisco la voce
    objf.voci[f.idx_voce-1]=objv
  else:	
    ## aggiungi voce!!!
    objf.aggiungi(objv)
  
  ## salvo data e scontrini
  objf.n_scontr1=f.n_scontr1
  objf.n_scontr2=f.n_scontr2
  objf.n_scontr3=f.n_scontr3
  objf.dt=f.dtfatt
  session['fatt']=jsonpickle.encode(objf)
  
  return redirect(url_for('componi_fattura'))

@app.route('/annulla_fattura')
def annulla_fattura():
  objf=jsonpickle.decode(session['fatt'])
  id_cliente = objf.id_cliente
  session['fatt']=None
  session.pop('fatt')
  return redirect(url_for('fatture_cliente', id=id_cliente, page=0))

def salva_fattura(f):
  objf=jsonpickle.decode(session['fatt'])
  cli=db.session.query(Cliente).get(objf.id_cliente)
  if(objf.id == 0):
    # creo una nuova fattura
    fattura = Fattura(cli, objf.dt, objf.num)
    db.session.add(fattura)
  else:
    # modifico una fattura esistente
    fattura = db.session.query(Fattura).get(objf.id)
    for v in fattura.voci:
      db.session.delete(v)
  
  fattura.data=f.dtfatt
  fattura.n_scontr1=f.n_scontr1
  fattura.n_scontr2=f.n_scontr2
  fattura.n_scontr3=f.n_scontr3
  
  for objv in objf.voci:
    voce=VoceFattura(codart=objv.codart, descr=objv.descr, qta=objv.qta, prezzo=objv.prezzo, aliq=objv.aliq)
    fattura.voci.append(voce)
  
  db.session.commit()
  session['fatt']=None
  session.pop('fatt')
  
  flash('Fattura salvata correttamente', 'success')
  return redirect(url_for('vis_fattura', idfatt=fattura.id))

#@app.route('/cfattura/<int:idfatt>', methods=['GET'])
#def canc_fattura(idfatt):
  #fatt = db.session.query(FatturaTemp).get(idfatt)
  #id_cliente = fatt.cliente_id
  #if(fatt==None):
    #abort(404)
    
  #db.session.delete(fatt)
  #db.session.commit()
  #return redirect(url_for('fatture_cliente', id=id_cliente, page=0))

@app.route('/modifica_voce/<int:index>', methods=['GET'])
def modifica_voce(index):
  fatt=jsonpickle.decode(session['fatt'])
  v=fatt.voci[index-1]
  return redirect(url_for('componi_fattura',_anchor='form',codart=v.codart,descr=v.descr,qta=v.qta,prezzo=v.prezzo,aliq=v.aliq,idx=index)) 

@app.route('/rimuovi_voce/<int:index>', methods=['GET'])
def rimuovi_voce(index):
  fatt=jsonpickle.decode(session['fatt'])
  fatt.rimuovi(index-1)
  session['fatt']=jsonpickle.encode(fatt)
  return redirect(url_for('componi_fattura',_anchor='form')) 
  
#@app.route('/dett_fattura/<int:id>')
#@login_required
#def dett_fattura(id, page=0):
  #pagenum = 20
  #offset = page * pagenum
  #f = Fattura.query.get(id)
  #return render_template('dett_fattura.html', fattura=f, voci=f.voci, tot=f.totale())

# jinja2 filters
@app.template_filter('dt')
def _jinja2_filter_date(date, fmt=None):
  if fmt:
    return date.strftime(fmt)  #format_date(date, fmt)
  else:
    return format_date(date, 'medium')

if __name__ == "__main__":
  #app.run(host='93.186.254.106', port=80)
  app.run()