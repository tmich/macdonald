# all the imports
import os, config, models, json
from functools import wraps
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# login manager
login_manager = LoginManager()
login_manager.init_app(app)

# mysql
mysql = MySQL(app)
db = models.Db(mysql)

@login_manager.user_loader
def load_user(user_id):
  return db.get_utente_by_id(user_id)

@app.route("/")
def main():
  return render_template('index.html')

@app.route('/utenti')
#@login_required
def utenti():
  utenti = db.get_utenti()
  aziende = db.get_aziende()
  return render_template('utenti.html', utenti=utenti, aziende=aziende)

@app.route('/clienti')
@app.route('/clienti/<int:page>')
#@login_required
def clienti(page=0):
  #return 'Autenticato' if current_user.is_authenticated else 'NON AUTENTICATO'
  clienti = db.get_clienti(page*50)
  return render_template('clienti.html', clienti=clienti, page=page)

@app.route('/cliente/<int:codice>')
#@login_required
def cliente(codice):
  cliente = db.get_cliente(codice)
  return render_template('cliente.html', cliente=cliente)

@app.route('/cliente/nuovo', methods=['GET', 'POST'])
def nuovo_cliente():
  if request.method == 'POST':
    f = request.form
    r = db.crea_cliente(str(f['ragione_sociale']), str(f['indirizzo']), str(f['cap']), str(f['citta']), str(f['p_iva']), str(f['cod_fiscale']), str(f['telefono']), str(f['email']))
    return str(r)
    flash('Creata nuova anagrafica cliente')
    return 'ok'
      #return redirect(url_for('clienti'))
    
  return render_template('cliente.html', cliente=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST':
    #l = models.Login(db)
    #u = l.login(request.form['username'], request.form['password']) 
    
    u = db.get_utente(request.form['username'], request.form['password'])
    if u == None:
      error = 'Nome utente o password errati'
    else:
      #session['logged_in'] = True
      #session['utente'] = json.dumps(u.__dict__)
      #g.utente = u
      login_user(u)
      u.is_authenticated = True
      flash('Accesso effettuato come {}'.format(u.username))
      return redirect(url_for('main'))
  return render_template('login.html', error=error)

@app.route('/logout')
def logout():
  logout_user()
  flash('You were logged out')
  return redirect(url_for('login'))

if __name__ == "__main__":
  app.run()