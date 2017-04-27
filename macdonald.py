# all the imports
import os, config, models
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

# mysql configuration
mysql = MySQL(app)
db = models.Db(mysql)

@app.route("/")
def main():
  return render_template('index.html')

@app.route('/utenti')
def utenti():
  utenti = db.get_utenti()
  aziende = db.get_aziende()
  return render_template('utenti.html', utenti=utenti, aziende=aziende)

@app.route('/clienti')
@app.route('/clienti/<int:page>')
def clienti(page=0):
  clienti = db.get_clienti(page*50)
  return render_template('clienti.html', clienti=clienti, page=page)

@app.route('/cliente/<int:codice>')
def cliente(codice):
  cliente = db.get_cliente(codice)
  return render_template('cliente.html', cliente=cliente)

@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST':
    if request.form['username'] != app.config['USERNAME']:
      error = 'Invalid username'
    elif request.form['password'] != app.config['PASSWORD']:
      error = 'Invalid password'
    else:
      session['logged_in'] = True
      flash('You were logged in')
      return redirect(url_for('show_entries'))
  return render_template('login.html', error=error)

@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  flash('You were logged out')
  return redirect(url_for('show_entries'))

if __name__ == "__main__":
  app.run()