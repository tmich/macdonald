# all the imports
import os, config, models, json
from functools import wraps
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask_mysqldb import MySQL
#from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# login manager
#login_manager = LoginManager()
#login_manager.init_app(app)

# mysql
mysql = MySQL(app)
db = models.Db(mysql)

#@login_manager.user_loader
#def load_user(user_id):
#  return db.get_utente_by_id(user_id)

@app.before_request
def load_user():
  if "user_id" in session:
    user = db.get_utente_by_id(session['user_id'])
  else:
    user = {'id' : 0, 'nome': 'Guest'}  # Make it better, use an anonymous User instead

  g.user = user

@app.route("/")
def main():
  return render_template('index.html', utente=g.user)

@app.route('/utenti')
#@login_required
def utenti():
  utenti = db.get_utenti()
  aziende = db.get_aziende()
  return render_template('utenti.html', utenti=utenti, aziende=aziende, utente=g.user)

@app.route('/clienti')
@app.route('/clienti/<int:page>')
#@login_required
def clienti(page=0):
  #return 'Autenticato' if current_user.is_authenticated else 'NON AUTENTICATO'
  clienti = db.get_clienti(page*50)
  return render_template('clienti.html', clienti=clienti, page=page, utente=g.user)


@app.route('/salva_cliente', methods=['POST'])
#@login_required
def salva_cliente():
  if request.method == 'POST':
    f = request.form
    if 'codice' in f:
      r = db.modifica_cliente(str(f['codice']), str(f['ragione_sociale']), str(f['indirizzo']), str(f['cap']), str(f['citta']), str(f['p_iva']), str(f['cod_fiscale']), str(f['telefono']), str(f['email']))
    else:
      r = db.crea_cliente(str(f['ragione_sociale']), str(f['indirizzo']), str(f['cap']), str(f['citta']), str(f['p_iva']), str(f['cod_fiscale']), str(f['telefono']), str(f['email']))
    #return str(r)
    flash('Anagrafica cliente salvata')
    #return 'ok'
    return redirect(url_for('clienti'))
  
@app.route('/cliente/<int:codice>')
#@login_required
def cliente(codice):
    cliente = db.get_cliente(codice)
    return render_template('cliente.html', cliente=cliente, utente=g.user)

@app.route('/nuovo_cliente', methods=['GET', 'POST'])
def nuovo_cliente():
  if request.method == 'POST':
    f = request.form
    r = db.crea_cliente(str(f['ragione_sociale']), str(f['indirizzo']), str(f['cap']), str(f['citta']), str(f['p_iva']), str(f['cod_fiscale']), str(f['telefono']), str(f['email']))
    #return str(r)#@app.route('/cliente/nuovo', methods=['GET', 'POST'])
#def nuovo_cliente():
  #if request.method == 'POST':
    #f = request.form
    #r = db.crea_cliente(str(f['ragione_sociale']), str(f['indirizzo']), str(f['cap']), str(f['citta']), str(f['p_iva']), str(f['cod_fiscale']), str(f['telefono']), str(f['email']))
    ##return str(r)
    #flash('Creata nuova anagrafica cliente')
    ##return 'ok'
    #return redirect(url_for('clienti'))
    
  #return render_template('cliente.html', cliente=None, utente=g.user)
    flash('Creata nuova anagrafica cliente')
    #return 'ok'
    return redirect(url_for('clienti'))
    
  return render_template('cliente.html', cliente=None, utente=g.user)

@app.route('/login', methods=['POST'])
def login():
  error = None
  if request.method == 'POST':
    u = db.get_utente(request.form['username'], request.form['password'])
    if u == None:
      error = 'Nome utente o password errati'
    else:
      session['logged_in'] = True
      session['user_id'] = u.id
      #flash('Accesso effettuato come {}'.format(u.username))
      return redirect(url_for('main'))
  #return render_template('login.html', error=error, utente=g.user)

@app.route('/logout')
def logout():
  #logout_user()
  g.utente = None
  session['logged_in'] = False
  if 'user_id' in session:
    session.pop('user_id')
  flash('Sessione di lavoro chiusa')
  return redirect(url_for('main'))

if __name__ == "__main__":
  app.run()