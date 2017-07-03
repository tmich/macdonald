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
from forms import FormNuovaFattura, FormAggiungiVoce, FormNuovaFattura, FormCliente, FormProdotto, FormProfilo, FormDate, FormDateFatture
import jsonpickle
from smtplib import SMTPException, SMTPAuthenticationError, SMTPRecipientsRefused
from sqlalchemy import and_, or_, func, distinct
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
	q = None
	pagenum = 50
	offset = page * pagenum
	cnt = db.session.query(Cliente).count()
	selezionabile=False
	
	if('id_fattura_cambio_cliente' in session):
		selezionabile=True
	
	if('qry_cliente' in session):
		q = session.get('qry_cliente')
		cnt = db.session.query(Cliente).filter(Cliente.ragsoc.like('%'+q+'%')).order_by('ragsoc').count()
		clienti = db.session.query(Cliente).filter(Cliente.ragsoc.like('%'+q+'%')).order_by('ragsoc').offset(offset).limit(pagenum)
	else:
		clienti = db.session.query(Cliente).order_by('ragsoc').offset(offset).limit(pagenum)
		
	last_page = cnt / pagenum
	return render_template('clienti.html', clienti=clienti, page=page, cnt=cnt, last_page=last_page, query=q, selezionabile=selezionabile)

@app.route('/cerca_cliente', methods=['GET','POST'])
@login_required
def cerca_cliente():
	if request.method == 'POST':
		f = request.form
		q = str(f['query'])
		session['qry_cliente']=q
	else:
		q = session.get('qry_cliente', '___')
	
	return redirect(url_for('clienti'))

@app.route('/annulla_ricerca_cliente', methods=['GET'])
@login_required
def annulla_ricerca_cliente():
	if('qry_cliente' in session):
		session.pop('qry_cliente')
	return redirect(url_for('clienti'))

@app.route('/salva_cliente', methods=['POST'])
@login_required
def salva_cliente():
	errors=[]
	id=0
	if request.method == 'POST':
		f = request.form
		form = FormCliente(f)
		id = f.get('id', 0)
	
		if(form.valido()):
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
		else:
			errors=form.errors
			ragsoc=form.ragsoc
			indirizzo=form.indirizzo
			cap=form.cap
			citta=form.citta
			piva=form.piva
			cfisc=form.cfisc
			telefono=form.telefono
			email=form.email
		
	return render_template('cliente.html',errors=errors,id=id,ragsoc=ragsoc,indirizzo=indirizzo,cap=cap,citta=citta,piva=piva,cfisc=cfisc,telefono=telefono,email=email)


@app.route('/nuovo_cliente', methods=['GET', 'POST'])
@login_required
def nuovo_cliente():
	errors=[]
	id=0
	ragsoc=""
	indirizzo=""
	cap=""
	citta=""
	piva=""
	cfisc=""
	telefono=""
	email=""
  
	if request.method == 'POST':
		f = request.form
		form = FormCliente(f)
	
		if(form.valido()):
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
			flash('Anagrafica cliente creata', 'success')
			#return redirect(url_for('clienti'))
			return redirect(url_for('cliente', id=cli.id))			
		else:
			errors=form.errors
			ragsoc=form.ragsoc
			indirizzo=form.indirizzo
			cap=form.cap
			citta=form.citta
			piva=form.piva
			cfisc=form.cfisc
			telefono=form.telefono
			email=form.email
		
	return render_template('cliente.html',errors=errors,id=id,ragsoc=ragsoc,indirizzo=indirizzo,cap=cap,citta=citta,piva=piva,cfisc=cfisc,telefono=telefono,email=email)

@app.route('/cliente/<int:id>')
@login_required
def cliente(id):
	cli = Cliente.query.get(id)
	
	ragsoc=cli.ragsoc
	indirizzo=cli.indirizzo
	cap=cli.cap
	citta=cli.citta
	piva=cli.p_iva
	cfisc=cli.cod_fisc
	telefono=cli.tel
	email=cli.email
	return render_template('cliente.html',errors=[],id=id,ragsoc=ragsoc,indirizzo=indirizzo,cap=cap,citta=citta,piva=piva,cfisc=cfisc,telefono=telefono,email=email)

@app.route('/prodotti', methods=['GET'])
@login_required
def prodotti():
	q = None
	cnt = db.session.query(Prodotto).count()
	if('qry_articolo' in session):
		q = session.get('qry_articolo')
		prodotti = db.session.query(Prodotto).filter(Prodotto.descr.like('%'+q+'%')).order_by('descr')
		cnt = prodotti.count()
	else:
		prodotti = db.session.query(Prodotto).order_by('descr')
	return render_template('prodotti.html', prodotti=prodotti, cnt=cnt, query=q)

@app.route('/annulla_ricerca_prodotto', methods=['GET'])
@login_required
def annulla_ricerca_prodotto():
	if('qry_articolo' in session):
		session.pop('qry_articolo')
	return redirect(url_for('prodotti'))

@app.route('/prodotto/<int:id>')
@login_required
def prodotto(id):
  p = Prodotto.query.get(id)
  return render_template('prodotto.html', id=p.id,descr=p.descr,codice=p.codice,aliq=p.aliq,prezzo=p.prezzo)

@app.route('/cerca_prodotto', methods=['GET','POST'])
@login_required
def cerca_prodotto(page=0):
	pagenum = 50
	offset=0
	
	if request.method == 'POST':
		f = request.form
		q = str(f['query'])
		session['qry_articolo']=q
	else:
		q = session.get('qry_articolo', '___')
	
	return redirect(url_for('prodotti'))
  
@app.route('/nuovo_prodotto')
@login_required
def nuovo_prodotto():
  return render_template('prodotto.html', id=0)

@app.route('/salva_prodotto', methods=['POST'])
@login_required
def salva_prodotto():
	errors=[]
	id=0
	codice=""
	descr=""
	aliq=""
	prezzo=""
	
	if request.method == 'POST':
		form = FormProdotto(request.form)
		id=form.id
		codice=form.codice
		descr=form.descrizione
		aliq=form.aliquota
		prezzo=form.prezzo
		
		if form.valido():
			if form.id > 0:
				p = Prodotto.query.get(form.id)
			else:
				p=Prodotto()
			
			p.codice = form.codice
			p.descr = form.descrizione
			p.aliq = form.aliquota
			p.prezzo = form.prezzo
			
			if form.id == 0:
				db.session.add(p)
			
			db.session.commit()
			
			flash('Articolo aggiornato', 'success')
		else:
			flash('Ci sono degli errori. Controllare e riprovare.', 'danger')
			return render_template('prodotto.html',errors=form.errors,id=id,descr=descr,codice=codice,aliq=aliq,prezzo=prezzo)

	return redirect(url_for('prodotto', id=p.id))
	
@app.route('/profilo', methods=['GET', 'POST'])
@login_required
def profilo():
	id=g.user.id
	username=g.user.username
	nome=g.user.nome
	email=g.user.email
	errors=dict()
	
	if request.method == 'POST':
		f = FormProfilo(request.form)
		id=f.user_id
		username=f.username
		nome=f.nome
		email=f.email
		
		if f.valido():
			u = User.query.get(f.user_id)
			u.nome = f.nome
			u.email = f.email
			
			if f.password_cambiata:
				u.password = f.nuova_pwd
				
			db.session.commit()
			
			flash('Profilo utente aggiornato', 'success')
		else:
			errors = f.errors
	return render_template('profilo.html', id=id, username=username, nome=nome, email=email, errors=errors)
  
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
  return render_template('fatture_da_inviare.html', fatture_da_inviare=fatture_da_inviare, cnt=len(fatture_da_inviare), current='fatture_da_inviare')
  
@login_required
@app.route('/fatture_inviate', methods=['GET'])
def fatture_inviate():
  fatture_inviate=db.session.query(InvioFattura).filter(InvioFattura.data_invio != None).all()
  return render_template('fatture_inviate.html', fatture_inviate=fatture_inviate, cnt=len(fatture_inviate), current='fatture_inviate')

@login_required
@app.route('/invia_tutte', methods=['GET'])
def invia_tutte():
	fatture_da_inviare=db.session.query(InvioFattura).filter_by(data_invio=None).all()
	min_righe=10
	dest = request.args.get('next')
	errors = []
  
	for inv in fatture_da_inviare:
		subject = "Fattura n. %d del %s" % (inv.fattura.num, inv.fattura.data.strftime("%d/%m/%Y"))
		recipient = inv.email
		mail_to_be_sent = Message(subject=subject, recipients=[recipient])
		body = 		  "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
		body = body + "e-mail: aldomd@inwind.it\n"
		body = body + "########################\n"
		body = body + "ORARIO NEGOZIO: 9.00/13.00 -.- 15.30/17.00\n"
		body = body + "SABATO: chiuso\n"
		body = body + "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n"
		body = body + "Alleghiamo alla presente ns. fattura.\nCogliamo l'occasione per inviare cordiali saluti.\n\n"
		body = body + "Cartoleria Macdonald Vittorio & C. snc\n"
		mail_to_be_sent.body = body
		n_righe = max(len(inv.fattura.voci), min_righe) - min(len(inv.fattura.voci), min_righe)
		pdf=create_pdf(render_template('fattura_pdf.html', fattura=inv.fattura, n_righe=n_righe))
		mail_to_be_sent.attach("fattura.pdf", "application/pdf", pdf.getvalue())
	
		try:
			mail_ext.send(mail_to_be_sent)
			inv.data_invio=datetime.datetime.now()
			inv.esito=0
		except SMTPAuthenticationError:
			errors.append('Fattura %d: errore nell\'autenticazione con il server di posta' % inv.fattura.num)
			inv.esito=1
		except SMTPRecipientsRefused:
			errors.append("Fattura %d: impossibile inviare all'indirizzo specificato"% inv.fattura.num)
			inv.esito=2
		except SMTPException, e:
			errors.append('Fattura %d: errore non specificato' % inv.fattura.num)
			inv.esito=3
			
		db.session.commit()

	if(len(errors) == 0):
		flash('Fatture inviate correttamente', 'success')
	else:
		flash('Alcune fatture non sono state inviate', 'warning')
		
	fatture_da_inviare=db.session.query(InvioFattura).filter_by(data_invio=None).all()
	return render_template('fatture_da_inviare.html', fatture_da_inviare=fatture_da_inviare, cnt=len(fatture_da_inviare), errors=errors)

@app.route('/invio_fatt/<int:idfatt>', methods=['GET'])
@login_required
def invia_fattura(idfatt):
	fatt = db.session.query(Fattura).get(idfatt)
	invio_fatt=InvioFattura(fatt, fatt.cliente.email)
	db.session.add(invio_fatt)
	db.session.commit()
	flash('Invio fattura prenotato con successo', 'success')
	#dest = request.args.get('next')
	#return redirect(dest)
	return redirect(url_for('vis_fattura', idfatt=fatt.id))

@app.route('/annulla_invio/<int:id>')
@login_required
def annulla_invio(id):
	invio = db.session.query(InvioFattura).get(id)
	db.session.delete(invio)
	db.session.commit()
	flash('Invio annullato', 'success')
	return redirect(url_for('fatture_da_inviare'))
  
#@login_required
#@app.route('/dfattura/<int:idfatt>', methods=['GET'])
#def del_fattura(idfatt):
  #fatt = db.session.query(Fattura).get(idfatt)
  #db.session.delete(fatt)
  #db.session.commit()
  #dest = request.args.get('next')
  #return redirect(dest)
  
@app.route('/fatture_da_stampare', methods=['GET'])
@login_required
def fatture_da_stampare():
	fatture_da_stampare = db.session.query(Fattura).filter(Fattura.stampato==0).order_by(Fattura.num)
	return render_template('fatture_da_stampare.html', fatture_da_stampare=fatture_da_stampare, cnt=fatture_da_stampare.count())

@app.route('/stampa_tutte', methods=['GET'])
@login_required
def stampa_tutte():
	fatture_da_stampare = db.session.query(Fattura).filter(Fattura.stampato==0)
	min_righe=10
	stringone=""
	anag = db.session.query(Anagrafica).get(1)
	for fattura in fatture_da_stampare:
		n_righe = max(len(fattura.voci), min_righe) - min(len(fattura.voci), min_righe)
		stringone = stringone + render_template('fattura_pdf.html', fattura=fattura, n_righe=n_righe, ragsoc=anag.ragsoc, descr=anag.descr, indirizzo=anag.indirizzo, mf=anag.mf)
		fattura.stampato=1
	
	pdf=create_pdf(stringone)
	response=make_response(pdf.getvalue())
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=stampa_fatture.pdf'
		
	db.session.commit()

	return response
	
@app.route('/stampa_fatt/<int:idfatt>', methods=['GET'])
@login_required
def stampa_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  min_righe=10
  n_righe = max(len(fatt.voci), min_righe) - min(len(fatt.voci), min_righe)
  anag = db.session.query(Anagrafica).get(1)

  pdf=create_pdf(render_template('fattura_pdf.html', fattura=fatt, n_righe=n_righe, ragsoc=anag.ragsoc, descr=anag.descr, indirizzo=anag.indirizzo, mf=anag.mf))
  response=make_response(pdf.getvalue())
  response.headers['Content-Type'] = 'application/pdf'
  response.headers['Content-Disposition'] = 'inline; filename=fattura.pdf'
  return response

@app.route('/vfattura/<int:idfatt>', methods=['GET'])
@login_required
def vis_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  return render_template('vfattura.html',fattura=fatt)

@app.route('/nuova_fattura/<int:id_cliente>', methods=['GET','POST'])
@login_required
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

@app.route('/cambia_cliente_fattura/<int:idfatt>')
@app.route('/cambia_cliente_fattura/<int:idfatt>/<int:idcli>')
@login_required
def cambia_cliente_fattura(idfatt,idcli=0):
	if(idcli == 0):
		session['id_fattura_cambio_cliente'] = idfatt
		return redirect(url_for('clienti', page=0))
	else:
		if 'id_fattura_cambio_cliente' in session:
			id_fattura_cambio_cliente = session.pop('id_fattura_cambio_cliente')
			objf=jsonpickle.decode(session['fatt'])
			objf.id_cliente = idcli
			session['fatt']=jsonpickle.encode(objf)
			return redirect(url_for('componi_fattura'))

@app.route('/modifica_fattura/<int:id>')
@login_required
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

def format_float(fl, separator='.'):
  return '{0:.2f}'.format(fl)  
  
@app.route('/componi_fattura', methods=['GET','POST'])
@login_required
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
  
  if 'id_fattura_cambio_cliente' in session:
	session.pop('id_fattura_cambio_cliente')
  
  #if(request.method=='GET'):
  if('idx' in request.args):
	idx_voce=request.args.get('idx')
	codart=request.args.get('codart')
	descr=request.args.get('descr')
	qta=request.args.get('qta')
	prezzo=format_float(float(request.args.get('prezzo', 0)))
	aliq=request.args.get('aliq')
  
  if(request.method=='POST'):
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
		  
  return render_template('componi_fattura.html',errors=errors,idfatt=fatt.id,datafattura=fatt.dt,numfatt=fatt.num,n_scontr1=fatt.n_scontr1,n_scontr2=fatt.n_scontr2,n_scontr3=fatt.n_scontr3,cliente=cli,imponibile=fatt.imponibile(),iva=fatt.iva(),totale=fatt.totale(),voci=fatt.voci,codart=codart,descr=descr,qta=qta,prezzo=prezzo,aliq=aliq,idx_voce=idx_voce)  

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
  id_fatt = objf.id
  id_cliente = objf.id_cliente
  session['fatt']=None
  session.pop('fatt')
  return redirect(url_for('cliente', id=id_cliente))

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
  
  fattura.cliente_id=objf.id_cliente
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

@app.route('/lista_fatture', methods=['GET', 'POST'])
def lista_fatture():
	errors=dict()
	if request.method=='POST':
		f=FormDate(request.form)
		if f.valido():
			fatture = db.session.query(Fattura).filter(Fattura.data.between(f.data_inizio, f.data_fine)).order_by(Fattura.num)
			return render_template('lista_fatture.html', fatture=fatture, data_inizio=f.data_inizio, data_fine=f.data_fine, cnt=fatture.count())
		else:
			errors=f.errors
	return render_template('form_date.html', errors=errors, titolo='Lista fatture', data_inizio=datetime.datetime.today(), data_fine=datetime.datetime.today(), cnt=0, current='lista_fatture')

@app.route('/ristampa_fatture', methods=['GET', 'POST'])
def ristampa_fatture():
	errors=dict()
	today = datetime.date.today()
	#first_of_month=today.replace(day=1)
	yesterday = today - datetime.timedelta(days=1)
	
	if request.method=='POST':
		f=FormDateFatture(request.form)
		if f.valido():
			#return repr(f.data_inizio) + ' ' + repr(f.data_fine) + ' ' + repr(f.nro_da) + ' ' + repr(f.nro_a) + ' ' + repr(f.anno)
			if f.nro_da > 0 and f.nro_a > 0 and f.anno > 0:
				fatture = db.session.query(Fattura).filter(and_(db.func.year(Fattura.data)==f.anno, Fattura.num.between(f.nro_da, f.nro_a))).order_by(Fattura.num)
			else:
				fatture = db.session.query(Fattura).filter(Fattura.data.between(f.data_inizio, f.data_fine)).order_by(Fattura.num)
			#return render_template('lista_fatture.html', fatture=fatture, data_inizio=f.data_inizio, data_fine=f.data_fine)
			min_righe=10
			stringone=""
			anag = db.session.query(Anagrafica).get(1)
			for fatt in fatture:
				n_righe = max(len(fatt.voci), min_righe) - min(len(fatt.voci), min_righe)
				stringone = stringone + render_template('fattura_pdf.html', fattura=fatt, n_righe=n_righe, ragsoc=anag.ragsoc, descr=anag.descr, indirizzo=anag.indirizzo, mf=anag.mf)
			
			pdf=create_pdf(stringone)
			response=make_response(pdf.getvalue())
			response.headers['Content-Type'] = 'application/pdf'
			response.headers['Content-Disposition'] = 'inline; filename=stampa_fatture.pdf'
			return response
		else:
			errors=f.errors
	return render_template('form_date_fatture.html', errors=errors, titolo='Ristampa fatture', data_inizio=yesterday, data_fine=today, anno=datetime.datetime.today().year, current='ristampa_fatture')

@app.route('/contatori', methods=['GET'])
@login_required
def contatori():
	#sql = text('select distinct(year(data)) from fattura')
	result = db.session.query(distinct(func.year(Fattura.data))).order_by(func.year(Fattura.data).desc())
	#result = db.engine.execute(sql)
	anni = []
	for row in result:
		anni.append(row[0])
	#print(anni, file=sys.stderr)
	return render_template('contatori.html', anni=anni, current='contatori')
	#return 'ook'

@app.route('/contatori/<int:anno>', methods=['GET', 'POST'])
@login_required
def contatori_per_anno(anno):
	ultima_fattura = db.session.query(func.max(Fattura.num)).filter(func.year(Fattura.data)==anno).scalar()
	ultima_fattura_stampata = db.session.query(func.max(Fattura.num)).filter(and_(func.year(Fattura.data)==anno, Fattura.stampato==1)).scalar()
	
	if request.method=='POST':
		f=request.form
		ufs=int(f.get('ufs', 0))
		
		if(ufs < ultima_fattura_stampata):
			fatture = fatt=db.session.query(Fattura).filter(and_(func.year(Fattura.data)==anno, Fattura.num > ufs))
			for fatt in fatture:
				print(fatt.num, file=sys.stderr)
				fatt.stampato=0
		else:
			fatture = fatt=db.session.query(Fattura).filter(and_(func.year(Fattura.data)==anno, Fattura.num > ultima_fattura_stampata, Fattura.num <= ufs))
			for fatt in fatture:
				print(fatt.num, file=sys.stderr)
				fatt.stampato=1
		db.session.commit()
		flash('Contatori aggiornati correttamente', 'success')
		ultima_fattura_stampata = db.session.query(func.max(Fattura.num)).filter(and_(func.year(Fattura.data)==anno, Fattura.stampato==1)).scalar()
	
	return render_template('contatori_per_anno.html', anno=anno, ultima_fattura=int(ultima_fattura), ultima_fattura_stampata=int(ultima_fattura_stampata), current='contatori')

@app.route('/anagrafica', methods=['GET', 'POST'])
@login_required
def anagrafica():
	anag=db.session.query(Anagrafica).first()
	if request.method == 'POST':
		f=request.form
		id=f['id']
		ragsoc=f['ragsoc']
		p_iva=f['p_iva']
		cod_fisc=f['cod_fisc']
		indirizzo=f['indirizzo']
		citta=f['citta']
		cap=f['cap']
		prov=f['prov']
		tel=f['tel']
		mf=f['mf']
		fax=f['fax']
		email=f['email']
		
		anag.ragsoc=ragsoc
		anag.p_iva=p_iva
		anag.cod_fisc=cod_fisc
		anag.indirizzo=indirizzo
		anag.cap=cap
		anag.prov=prov
		anag.tel=tel
		anag.mf=mf
		anag.fax=fax
		anag.email=email
		
		db.session.commit()
		flash('Anagrafica aggiornata', 'success')
	
	return render_template('anagrafica.html', id=anag.id, ragsoc=anag.ragsoc, p_iva=anag.p_iva, cod_fisc=anag.cod_fisc, indirizzo=anag.indirizzo, citta=anag.citta, cap=anag.cap, prov=anag.prov, tel=anag.tel, mf=anag.mf, fax=anag.fax, email=anag.email)

@app.route('/elimina_inviate', methods=['POST'])
@login_required
def elimina_inviate():
	f=request.form
	# for k in f:
		# print("%s=%s\n" % (k, f[k]), file=sys.stderr)
	ids = f.getlist("da_eliminare")
	for id in ids:
		# print("%s\n" % (id), file=sys.stderr)
		inv=db.session.query(InvioFattura).get(id)
		db.session.delete(inv)
	db.session.commit()
	flash("Invii eliminati", "success")
	return redirect(request.args.get('next'));
	
# jinja2 filters
@app.template_filter('dt')
def _jinja2_filter_date(date, fmt=None):
  if fmt:
	return date.strftime(fmt)  #format_date(date, fmt)
  else:
	return format_date(date, 'medium')

if __name__ == "__main__":
  app.run(host='93.186.254.106', port=80)
  #app.run(host='93.186.254.106', port=5000)
  #app.run(host='192.168.56.2', port=5000)
  #app.run()
