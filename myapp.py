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
from models import db, Anagrafica, Cliente, Prodotto, Fattura, VoceFattura, InvioFattura, User, FatturaSequence, ObjFatt, ObjVoce, EmailConfig, Messaggio, ListaDistribuzione, MembroListaDistribuzione, get_azienda, InvioFatturaElettronica
from forms import FormNuovaFattura, FormAggiungiVoce, FormNuovaFattura, FormCliente, FormProdotto, FormProfilo, FormDate, FormDateFatture
import jsonpickle
from smtplib import SMTPException, SMTPAuthenticationError, SMTPRecipientsRefused
from sqlalchemy import and_, or_, func, distinct
from threading import Thread
from fatturae import converti_fattura
import ftplib
import base64
import rpyc

def create_app():
	app = Flask(__name__)
	#app.config.from_object('config.DevelopmentConfig')
	app.config.from_object(config.get_config_name())
	app.static_folder = 'static' 
	#mail_ext = Mail(app)
	#db = SQLAlchemy(app)
	db.init_app(app)
	babel = Babel(app)
	#with app.app_context():
		#Extensions like Flask-SQLAlchemy now know what the "current" app
		#is while within this block. Therefore, you can now run........
		#db.create___all()

	return app

app = create_app()
	
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
	n_fatture_da_inviare = db.session.query(InvioFattura).filter(InvioFattura.data_invio==None).count()
	n_fatture_da_stampare = db.session.query(Fattura).filter(Fattura.stampato==0).count()
	return render_template('index.html', n_fatture_da_inviare=n_fatture_da_inviare, n_fatture_da_stampare=n_fatture_da_stampare, current='home')

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
 
def is_number(s):
	try:
		int(s)
		return True
	except ValueError:
		return False
 
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
	
		filter1 = Cliente.p_iva == str(q)
		filter2 = Cliente.ragsoc.like('%'+q+'%')
		filter3 = Cliente.cod_fisc.like(q+'%')
		
		qry = db.session.query(Cliente).filter(or_(filter1, filter2, filter3)).order_by('ragsoc')
		cnt = qry.count()
		clienti = qry.offset(offset).limit(pagenum)
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
			pec = f['pec']
			cod_dest = f['cod_dest']
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
			cli.pec = pec
			cli.cod_destinatario = cod_dest
			
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
			pec=form.pec
			cod_dest=form.cod_dest
			flash('Alcuni dati non sono validi, verificare', 'danger')
		
	return render_template('cliente.html',errors=errors,id=id,ragsoc=ragsoc,indirizzo=indirizzo,cap=cap,citta=citta,piva=piva,cfisc=cfisc,telefono=telefono,email=email,pec=pec,cod_dest=cod_dest)


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
	pec=cli.pec if cli.pec != None else ''
	cod_dest=cli.cod_destinatario if cli.cod_destinatario != None else ''
	return render_template('cliente.html',errors=[],id=id,ragsoc=ragsoc,indirizzo=indirizzo,cap=cap,citta=citta,piva=piva,cfisc=cfisc,telefono=telefono,email=email,pec=pec,cod_dest=cod_dest)

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
  
@app.route('/elimina_prodotto/<int:id>')
@login_required
def elimina_prodotto(id):
  #return render_template('prodotto.html', id=0)
  p = Prodotto.query.get(id)
  db.session.delete(p)
  db.session.commit()
  flash('Articolo eliminato', 'success')
  
  return redirect(url_for('prodotti'))

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
	
@app.route('/utenti', methods=['GET', 'POST'])
@app.route('/utenti/<int:id>', methods=['GET', 'POST'])
@login_required
def utenti(id=0):
	if id==0:
		id=g.user.id
		username=g.user.username
		nome=g.user.nome
		email=g.user.email
	else:
		u=User.query.get(id)
		if not u:
			return redirect(url_for('utenti'))
		id=u.id
		username=u.username
		nome=u.nome
		email=u.email
		
	errors=dict()
	utenti = User.query.all()
	
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
	return render_template('utenti.html', id=id, username=username, nome=nome, email=email, errors=errors, utenti=utenti, current='utenti')

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
	return render_template('profilo.html', id=id, username=username, nome=nome, email=email, errors=errors, current='profilo')
  
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
  profili_email=db.session.query(EmailConfig).all()
  messaggi = db.session.query(Messaggio).filter_by(attivo=True)
  return render_template('fatture_da_inviare.html', fatture_da_inviare=fatture_da_inviare, cnt=len(fatture_da_inviare), profili_email=profili_email, messaggi=messaggi, current='fatture_da_inviare')
  
@login_required
@app.route('/fatture_inviate', methods=['GET'])
def fatture_inviate():
  fatture_inviate=db.session.query(InvioFattura).filter(InvioFattura.data_invio != None).all()
  return render_template('fatture_inviate.html', fatture_inviate=fatture_inviate, cnt=len(fatture_inviate), current='fatture_inviate')

@login_required
@app.route('/xml_fattura/<int:id>', methods=['GET'])
def xml_fattura(id):
  #print("ID: " + str(id))
  inv=db.session.query(InvioFatturaElettronica).get(id)
  return inv.xml

# @login_required
# @app.route('/profili_email', methods=['GET'])
# def profili_email():
	# profili = db.session.query(EmailConfig) #.filter_by(attivo=True).first()	
	# return render_template('profili_email.html', profili=profili)

@login_required
@app.route('/profilo_email/', methods=['GET'])
@app.route('/profilo_email/<int:id>', methods=['GET'])
def profilo_email(id=0):
	profili = db.session.query(EmailConfig)
	n_profili=db.session.query(EmailConfig).count()

	if(id > 0):
		profilo = profili.get(id)
	else:
		profilo = profili.first()	# filter_by(attivo=True)
	
	return render_template('profilo_email.html', profili=profili.all(), profilo=profilo, ultimo=n_profili == 1, current='profilo_email')

@login_required
@app.route('/profilo_email/new', methods=['GET'])
def nuovo_profilo_email():
	return render_template('profilo_email.html', nuovo=True, current='profilo_email')
	
@login_required
@app.route('/profilo_email', methods=['POST'])
def salva_profilo_email():
	f=request.form
	id=int(f.get('id', 0))
	email=f['email']
	nome=f['nome']
	username=f['username']
	password=f['password']
	server=f['server']
	porta=int(f.get('porta', 0))
	ssl=f.get('ssl', '') == 'on'
	tls=f.get('tls', '') == 'on'
	
	print('%s: %d' % ('salva_profilo_email', id), file=sys.stderr)
	
	if(id > 0):
		conf = EmailConfig.query.get(id)
		conf.email=email
		conf.nome=nome
		conf.username=username
		conf.password=password
		conf.server=server
		conf.porta=porta
		conf.ssl=ssl
		conf.tls=tls
		msg='Profilo email modificato correttamente'
	else:
		conf = EmailConfig(username, password, nome, server, email, porta, ssl, tls)
		db.session.add(conf)
		msg='Nuovo profilo email creato'
		
	db.session.commit()
	flash(msg, 'success')
	return redirect(url_for('profilo_email', current='profilo_email'))

@login_required
@app.route('/profilo_email/del/<int:id>', methods=['GET'])
def elimina_profilo_email(id):
	profilo = db.session.query(EmailConfig).get(id)
	db.session.delete(profilo)
	db.session.commit()
	flash('Profilo email eliminato', 'danger')
	return redirect(url_for('profilo_email', current='profilo_email'))
	
@login_required
@app.route('/invia_tutte', methods=['POST'])
def invia_tutte():
	form=request.form
	profilo_id=form['profilo']

	fatture_da_inviare=db.session.query(InvioFattura).filter_by(data_invio=None).all()
	#min_righe=10
	dest = request.args.get('next')
	errors = []
	
	# leggo il profilo email selezionato dal db
	conf = db.session.query(EmailConfig).get(profilo_id) #filter_by(attivo=True).first()
	app.config.update(
		MAIL_USE_SSL = conf.ssl,
		MAIL_USE_TLS = conf.tls,
		MAIL_SERVER = conf.server,
		MAIL_PORT = conf.porta,
		MAIL_DEFAULT_SENDER = (str(conf.nome), str(conf.email)),
		MAIL_USERNAME = str(conf.username),
		MAIL_PASSWORD = str(conf.password)
	)
	mail = Mail(app)
	
	with mail.connect() as conn:
		for inv in fatture_da_inviare:
			subject = "Fattura n. %d del %s" % (inv.fattura.num, inv.fattura.data.strftime("%d/%m/%Y"))
			recipient = inv.email
			mail_to_be_sent = Message(subject=subject, recipients=[recipient])
			msg_id = form['messaggio']
			m = Messaggio.query.get(msg_id)
			mail_to_be_sent.body = m.testo
			mail_to_be_sent.html = m.testo
			pdf=create_pdf(prepara_pdf(inv.fattura))
			mail_to_be_sent.attach("fattura.pdf", "application/pdf", pdf.getvalue())
		
			try:
				conn.send(mail_to_be_sent)
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
	
	return redirect(url_for('fatture_da_inviare'))

@app.route('/invio_fatt/<int:idfatt>', methods=['GET'])
@login_required
def invia_fattura(idfatt):
	fatt = db.session.query(Fattura).get(idfatt)
	invio_fatt=InvioFattura(fatt, fatt.cliente.email)
	db.session.add(invio_fatt)
	db.session.commit()
	flash('Invio fattura prenotato con successo', 'success')
	return redirect(url_for('vis_fattura', idfatt=fatt.id))

@app.route('/annulla_invio/<int:id>')
@login_required
def annulla_invio(id):
	invio = db.session.query(InvioFattura).get(id)
	db.session.delete(invio)
	db.session.commit()
	flash('Invio annullato', 'success')
	return redirect(url_for('fatture_da_inviare'))
 
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
	for fattura in fatture_da_stampare:
		stringone = stringone + prepara_pdf(fattura)
		fattura.stampato=1
	
	pdf=create_pdf(stringone)
	response=make_response(pdf.getvalue())
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=stampa_fatture.pdf'
		
	db.session.commit()

	return response

@app.route('/stampa_cliente/<int:idcliente>', methods=['GET'])
@login_required
def stampa_cliente(idcliente):
  cliente = db.session.query(Cliente).get(idcliente)
  pdf=create_pdf(render_template('cliente_pdf.html', c=cliente))
  response=make_response(pdf.getvalue())
  response.headers['Content-Type'] = 'application/pdf'
  response.headers['Content-Disposition'] = 'inline; filename=AnagraficaCliente.pdf'
  return response
	
@app.route('/stampa_fatt/<int:idfatt>', methods=['GET'])
@login_required
def stampa_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  pdf=create_pdf(prepara_pdf(fatt))
  response=make_response(pdf.getvalue())
  response.headers['Content-Type'] = 'application/pdf'
  response.headers['Content-Disposition'] = 'inline; filename=fattura.pdf'
  return response

def prepara_pdf(fatt):
  min_righe=12
  righe_vuote = min_righe - len(fatt.voci)
  pdf=render_template('fattura_pdf.html', fattura=fatt, n_righe=righe_vuote)
  return pdf
  
@app.route('/vfattura/<int:idfatt>', methods=['GET'])
@login_required
def vis_fattura(idfatt):
  fatt = db.session.query(Fattura).get(idfatt)
  trasmissibile = True
  data_ultima_trasmissione = None
  in_attesa = db.session.query(InvioFatturaElettronica).filter(InvioFatturaElettronica.fattura_id == idfatt).filter(InvioFatturaElettronica.data_invio == None).count()
  trasmesse = db.session.query(InvioFatturaElettronica).filter(InvioFatturaElettronica.fattura_id == idfatt).filter(InvioFatturaElettronica.data_invio != None)
  gia_trasmessa = trasmesse.count() > 0
  if gia_trasmessa:
	data_ultima_trasmissione = trasmesse.order_by(InvioFatturaElettronica.data_invio.desc()).first().data_invio
  if in_attesa > 0:
	trasmissibile = False
	
  return render_template('vfattura.html',fattura=fatt, trasmissibile=trasmissibile, gia_trasmessa=gia_trasmessa, data_ultima_trasmissione=data_ultima_trasmissione)

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
  fattura.azienda_id=objf.id_azienda
  
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
			for fatt in fatture:
				stringone = stringone + prepara_pdf(fatt)
			
			pdf=create_pdf(stringone)
			response=make_response(pdf.getvalue())
			response.headers['Content-Type'] = 'application/pdf'
			response.headers['Content-Disposition'] = 'inline; filename=stampa_fatture.pdf'
			return response
		else:
			errors=f.errors
	return render_template('form_date_fatture.html', errors=errors, titolo='Ristampa fatture', data_inizio=yesterday, data_fine=today, anno=datetime.datetime.today().year, current='ristampa_fatture')

@app.route('/messaggi/new', methods=['GET', 'POST'])
@login_required
def nuovo_messaggio():
	if request.method=='GET':
		return render_template('nuovo_messaggio.html', id=0, current='messaggi')
	else:
		f=request.form
		nome=f['nome']
		testo=f['testo']
		msg=Messaggio(nome, testo)
		db.session.add(msg)
		db.session.commit()
		flash('creato nuovo messaggio', 'success')
		return redirect(url_for('messaggi'))
		
	
@app.route('/messaggi', methods=['GET', 'POST'])
@app.route('/messaggi/<int:id>', methods=['GET', 'POST'])
@login_required
def messaggi(id=0):
	messaggi = db.session.query(Messaggio).filter_by(attivo=True)
	if request.method == 'GET':
		if id==0:
			msg=Messaggio(nome='',testo='')
		else:
			msg=db.session.query(Messaggio).get(id)
	else:
		f = request.form
		id = f['id']
		msg=db.session.query(Messaggio).get(id)
		msg.nome = f['nome']
		msg.testo = f['testo']
		db.session.commit()
		flash('Messaggio salvato con successo', 'success')
		
	return render_template('messaggi.html', messaggi=messaggi, id=id, testo=msg.testo, nome=msg.nome, current='messaggi')

@app.route('/elimina_messaggio/<int:id>', methods=['GET'])
def elimina_messaggio(id):
	msg=db.session.query(Messaggio).get(id)
	db.session.delete(msg)
	db.session.commit()
	flash('Messaggio eliminato', 'success')
		
	return redirect(url_for('messaggi'))
	

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
	
	return render_template('contatori_per_anno.html', anno=anno, ultima_fattura=int(ultima_fattura) if ultima_fattura != None else 0,
		ultima_fattura_stampata=int(ultima_fattura_stampata) if ultima_fattura_stampata != None else 0, current='contatori')

@app.route('/anagrafica', methods=['GET', 'POST'])
@login_required
def anagrafica():
	anag=get_azienda()
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
	
	return render_template('anagrafica.html', id=anag.id, ragsoc=anag.ragsoc, p_iva=anag.p_iva, cod_fisc=anag.cod_fisc, indirizzo=anag.indirizzo, citta=anag.citta, cap=anag.cap, prov=anag.prov, tel=anag.tel, mf=anag.mf, fax=anag.fax, email=anag.email, current='anagrafica')

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

@app.route('/modifica_email_invio', methods=['POST'])
@login_required
def modifica_email_invio():
	f=request.form
	id=f['id']
	email=f['email']
	inv=db.session.query(InvioFattura).get(id)
	inv.email=email
	db.session.commit()
	flash("Modifica effettuata", "success")
	return redirect(url_for('fatture_da_inviare'));

@app.route('/ricerca_clienti', methods=['GET', 'POST'])
@login_required
def ricerca_clienti():
	pagenum = 50
	page = int(request.args.get('page', 0))
	offset = page * pagenum
	cnt = db.session.query(Cliente).count()
	q = None
	
	if 'next' not in request.args:
		abort(404)
	
	args = request.args.copy()
	
	next = args.pop('next')
	
	if 'new' in args:
		args.pop('new')
		if 'qry_cliente' in session:
			session.pop('qry_cliente')
			
	if 'page' in args:
		args.pop('page')
	
	if(request.method == 'POST'):
		f = request.form
		q = f['query']
		session['qry_cliente'] = q
	else:
		if 'qry_cliente' in session:
			q = session['qry_cliente']
		
	if q != None:
		filter1 = Cliente.p_iva == str(q)
		filter2 = Cliente.ragsoc.like('%'+q+'%')
		filter3 = Cliente.cod_fisc.like(q+'%')
		
		qry = db.session.query(Cliente).filter(or_(filter1, filter2, filter3)).order_by('ragsoc')
		cnt = qry.count()
		clienti = qry.offset(offset).limit(pagenum)
	else:
		# if 'qry_cliente' in session:
			# session.pop('qry_cliente')
		clienti = db.session.query(Cliente).order_by('ragsoc').offset(offset).limit(pagenum)
		
	last_page = cnt / pagenum
	
	return render_template('ricerca_clienti.html', done=request.args['done'], done_arg=request.args['done_arg'], referrer=request.referrer, clienti=clienti, page=page, cnt=cnt, last_page=last_page, query=q, next=next, args=args)

@app.route('/liste_distribuzione', methods=['GET'])
@login_required
def liste_distribuzione():
  liste=db.session.query(ListaDistribuzione).filter_by(canc=0).all()
  return render_template('liste_distribuzione.html', liste=liste, cnt=len(liste), current='liste')
 
@app.route('/rinomina_lista_distribuzione/<int:id>', methods=['POST'])
@login_required
def rinomina_lista_distribuzione(id):
	lista=db.session.query(ListaDistribuzione).get(id)
	f=request.form
	nuovo_nome = f['nome']
	if nuovo_nome.strip() == '':
		flash("Inserire il nome della lista", "danger")
		return redirect(url_for('lista_distribuzione', id=id))
	lista.nome=nuovo_nome
	db.session.commit()
	flash('Lista rinominata in %s' % lista.nome, 'success')
	return redirect(url_for('lista_distribuzione', id=id))

@app.route('/lista_distribuzione', methods=['GET', 'POST'])
@login_required
def nuova_lista_distribuzione():
	if request.method=='GET':
		return render_template('nuova_lista_distribuzione.html', current='liste')
	else:
		f=request.form
		nuovo_nome = f['nome']
		if nuovo_nome.strip() == '':	
			flash("Inserire il nome della lista", "danger")
			return redirect(url_for('nuova_lista_distribuzione'))
		l=ListaDistribuzione(nome=nuovo_nome)
		db.session.add(l)
		db.session.commit()
		return redirect(url_for('lista_distribuzione', id=l.id))

@app.route('/elimina_lista_distribuzione/<int:id>', methods=['GET'])		
@login_required
def elimina_lista_distribuzione(id):
	lista=db.session.query(ListaDistribuzione).get(id)
	db.session.delete(lista)
	db.session.commit()
	flash('Lista eliminata', 'success')
	return redirect(url_for('liste_distribuzione'))
  
@app.route('/lista_distribuzione/<int:id>', methods=['GET', 'POST'])
@login_required
def lista_distribuzione(id):
	lista=db.session.query(ListaDistribuzione).get(id)
	# session['id_lista']=lista.id
	return render_template('lista_distribuzione.html', id=lista.id, nome=lista.nome, cnt=lista.membri.count(), membri=lista.membri, current='liste')

@app.route('/aggiungi_membro/<int:id_cliente>')
@login_required
def aggiungi_membro(id_cliente):
	if 'id_lista' not in request.args:
		abort(404)

	id_lista=request.args.get('id_lista')
	lista=db.session.query(ListaDistribuzione).get(id_lista)
	cliente=db.session.query(Cliente).get(id_cliente)

	if lista.membri.filter(MembroListaDistribuzione.cliente_id == id_cliente).count() == 0:
		membro=MembroListaDistribuzione(cliente_id=id_cliente,lista_id=id_lista,email=cliente.email)
		db.session.add(membro)
		db.session.commit()
		flash("%s aggiunto alla lista %s" % (cliente.ragsoc, lista.nome), 'success')
	else:
		flash("%s e' gia' presente nella lista %s" % (cliente.ragsoc, lista.nome), 'danger')
	return redirect(request.referrer)
	#return redirect(url_for('lista_distribuzione', id=id_lista))

@app.route('/rimuovi_membro/<int:id_membro>/<int:id_lista>')
@login_required	
def rimuovi_membro(id_membro, id_lista):
	lista=db.session.query(ListaDistribuzione).get(id_lista)
	if lista.membri.filter(MembroListaDistribuzione.id == id_membro).count() != 0:
		membro = db.session.query(MembroListaDistribuzione).get(id_membro)
		db.session.delete(membro)
		db.session.commit()
	return redirect(url_for('lista_distribuzione', id=id_lista))

@app.route('/nuova_comunicazione')
@login_required	
def nuova_comunicazione():
	liste=db.session.query(ListaDistribuzione).filter_by(canc=0).all()
	messaggi = db.session.query(Messaggio).filter_by(attivo=True)
	m=request.args.get('m', 0)
	l=request.args.get('l', 0)
	return render_template('nuova_comunicazione.html', liste=liste, messaggi=messaggi, mid=m,lid=l, current='nuova_comunicazione')

@app.route('/anteprima_comunicazione', methods=['POST'])
@login_required	
def anteprima_comunicazione():
	f=request.form
	id_lista=int(f['lista'])
	id_messaggio=int(f['messaggio'])
	
	if(id_messaggio==0):
		flash('Scegliere un messaggio', 'danger')
		return redirect(url_for('nuova_comunicazione', l=id_lista, m=id_messaggio))
	
	if(id_lista==0):
		flash('Scegliere una lista', 'danger')
		return redirect(url_for('nuova_comunicazione', l=id_lista, m=id_messaggio))
	
	profili=db.session.query(EmailConfig).all()
	lista=db.session.query(ListaDistribuzione).get(id_lista)
	messaggio=db.session.query(Messaggio).get(id_messaggio)
	
	return render_template('anteprima_comunicazione.html', profili_email=profili, lista=lista, messaggio=messaggio.testo, current='nuova_comunicazione')

@app.route('/invio_comunicazione', methods=['POST'])
@login_required	
def invio_comunicazione():
	print('invio_comunicazione', file=sys.stderr)
	f=request.form
	messaggio=f['messaggio']
	oggetto=f['oggetto']
	profilo_id=f['profilo']
	id_lista=f['lista']
	bcc=[]
	lista=db.session.query(ListaDistribuzione).get(id_lista)
	for m in lista.membri:
		bcc.append(m.email)
	
	invia_email(oggetto=oggetto, profilo_id=profilo_id,destinatari=[],bcc=bcc,testo='',html=messaggio)
	flash('Comunicazione inviata', 'success')
	return redirect(url_for('main'))
	
@app.route('/invio_fattura_elettronica/<int:idfatt>', methods=['GET'])
@login_required
def invio_fattura_elettronica(idfatt):
	fatt = db.session.query(Fattura).get(idfatt)
	invio_fatt=InvioFatturaElettronica(fatt)
	db.session.add(invio_fatt)
	db.session.commit()
	invio_fatt.xml = converti_fattura(fatt, invio_fatt.id)
	db.session.commit()
	flash('Trasmissione ad AGYO prenotata con successo', 'success')
	return redirect(url_for('vis_fattura', idfatt=fatt.id))

@login_required
@app.route('/fatture_elettroniche_da_inviare', methods=['GET'])
def fatture_elettroniche_da_inviare():
	fatture_da_inviare=db.session.query(InvioFatturaElettronica).filter_by(data_invio=None).all()
	return render_template('fatture_elettroniche_da_inviare.html', fatture_da_inviare=fatture_da_inviare, 
		cnt=len(fatture_da_inviare), current='fatture_elettroniche_da_inviare')
  
@login_required
@app.route('/fatture_elettroniche_inviate', methods=['GET'])
def fatture_elettroniche_inviate():
	fatture_inviate=db.session.query(InvioFatturaElettronica).join(InvioFatturaElettronica.fattura).filter(InvioFatturaElettronica.data_invio != None).order_by(Fattura.num.desc()).all()
	return render_template('fatture_elettroniche_inviate.html', fatture_inviate=fatture_inviate, 
		cnt=len(fatture_inviate), current='fatture_elettroniche_inviate')

@app.route('/annulla_invio_fattura_elettronica/<int:id>')
@login_required
def annulla_invio_fattura_elettronica(id):
	invio = db.session.query(InvioFatturaElettronica).get(id)
	db.session.delete(invio)
	db.session.commit()
	flash('Invio ad AGYO annullato', 'success')
	return redirect(url_for('fatture_elettroniche_da_inviare'))
	
@app.route('/elimina_fatture_elettroniche_inviate', methods=['POST'])
@login_required
def elimina_fatture_elettroniche_inviate():
	f=request.form
	ids = f.getlist("da_eliminare")
	for id in ids:
		inv=db.session.query(InvioFatturaElettronica).get(id)
		db.session.delete(inv)
	db.session.commit()
	flash("Invii ad AGYO eliminati", "success")
	return redirect(request.args.get('next'));
	
@app.route('/trasmetti_fatture_elettroniche', methods=['POST'])
@login_required	
def trasmetti_fatture_elettroniche():
	fatture_da_inviare=db.session.query(InvioFatturaElettronica).filter_by(data_invio=None).all()
	errors = []
	
	# ftps = ftplib.FTP_TLS()
	# ftps.connect('5.249.149.66', 2222)
	# ftps.login('aldo', 'aldo.2019')
	# ftps.prot_p()
	# ftps.cwd('/test_upload')
	# f = open('/home/tiziano/turni_dump_18072017.sql', 'rb')
	# ftps.storbinary('STOR test03.xml', f)
	# f.close()
	# ftps.quit()
	
	# Parametri di configurazione
	host = app.config['SERVIZIO_AGYO']
	port = app.config['PORTA_AGYO']
	test = app.config['DEVELOPMENT']
	
	for i in fatture_da_inviare:
		nomefile = 'IT' + i.fattura.azienda.p_iva + '_' + str(i.id) + '.xml'
		encoded = base64.b64encode(i.xml)
		print('Invio richiesta a ', host + ":" + port)
		c = rpyc.connect(host, port)
		risp = c.root.carica(encoded, nomefile, test)		# 0: 'File creato', -1: 'File esistente', -2: 'Unknown error'
		print('Ricevuta risposta da ' + host + ': ' + str(risp))
		i.esito = risp
		if risp == 0:
			i.data_invio = datetime.datetime.today()
		else:
			if risp == -1:
				errors.append('Fattura ' + str(i.fattura.num) + ' gia\' trasmessa' )
			else:
				errors.append('Fattura ' + str(i.fattura.num) + ': errore generico' )
	
	db.session.commit()
	
	if len(errors) == 0:
		flash('Fatture trasmesse con successo', 'success')
	else:
		err = 'Alcune fatture non sono state trasmesse: '
		for e in errors:
			err = err + e + '  -  '
		flash(err, 'warning')
	
	return redirect(url_for('fatture_elettroniche_da_inviare'))
	
	
# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xi-email-support
def invia_email_async(app, mail, msg):
	with app.app_context():
		mail.send(msg)
	
def invia_email(oggetto, profilo_id, destinatari, bcc, testo, html):
	# leggo il profilo email selezionato dal db
	conf = db.session.query(EmailConfig).get(profilo_id)
	app.config.update(
		MAIL_USE_SSL = conf.ssl,
		MAIL_USE_TLS = conf.tls,
		MAIL_SERVER = conf.server,
		MAIL_PORT = conf.porta,
		MAIL_DEFAULT_SENDER = (str(conf.nome), str(conf.email)),
		MAIL_USERNAME = str(conf.username),
		MAIL_PASSWORD = str(conf.password)
	)
	mail = Mail(app)
	msg = Message(oggetto, sender=conf.email, recipients=destinatari, bcc=bcc)
	msg.body = testo
	msg.html = html
	thr = Thread(target=invia_email_async, args=[app, mail, msg])
	thr.start()
	
# jinja2 filters
@app.template_filter('dt')
def _jinja2_filter_date(date, fmt=None):
  if fmt:
	return date.strftime(fmt)  #format_date(date, fmt)
  else:
	return format_date(date, 'medium')
	
if __name__ == "__main__":
  # SVILUPPO
  #app.run(host='80.211.227.37', port=80) 
  
  # PRODUZIONE
  #app.run(host='93.186.254.106', port=80)
  
  #app.run(host='93.186.254.106', port=5000)
  #app.run(host='192.168.56.2', port=5000)
  #app.run()
  pass
