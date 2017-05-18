# models.py

class Login(object):
  def __init__(self, db):
    self.db = db
    
  def login(self, username, password):
    return self.db.get_utente_by_username_and_password(username, password)

class Db(object):
  def __init__(self, mysql):
    self.mysql = mysql
  
  def get_utente_by_id(self, user_id):
    cur = self.mysql.connection.cursor()
    sql='''select `id`, `nome`, `username`, `profilo`, `attivo` from `utenti` where `id`=1'''#.format(user_id)
    cur.execute(sql)
    rv = cur.fetchone()
    if rv != None:
      u = Utente(rv[0], rv[1], rv[2], rv[3], rv[4])
      return u
    return None
  
  def get_utente(self, username, password):
    cur = self.mysql.connection.cursor()
    cur.execute('''select id, nome, username, profilo, attivo from `utenti` where username='{}' and password='{}' '''.format(username, password))
    rv = cur.fetchone()
    if rv != None:
      u = Utente(rv[0], rv[1], rv[2], rv[3], rv[4])
      return u
    return None
    
  def get_utenti(self):
    utenti = []
    cur = self.mysql.connection.cursor()
    cur.execute('''select id, nome, username, profilo, attivo from `utenti`''')
    for u in cur.fetchall():
      utenti.append(Utente(u[0], u[1], u[2], u[3], u[4]))
    return utenti
  
  def get_aziende(self):
    aziende = []
    cur = self.mysql.connection.cursor()
    cur.execute('''select id, Ragione_Sociale, Descr, PI, CF, Indirizzo, Citta, CAP, Provincia, Telefono, MF, Fax, E_mail from `anagrafica`''')
    for a in cur.fetchall():
      aziende.append(Azienda(a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],a[8],a[9],a[10],a[11],a[12]))
    return aziende  
  
  def get_clienti(self,offset=0,count=50):
    clienti = []
    cur = self.mysql.connection.cursor()
    cur.execute('''select cod, RagSoc, Ind, cap, citta, piva, cfisc, old_cod, tel, email from clienti order by RagSoc limit {}, {}'''.format(offset, count))
    for c in cur.fetchall():
      clienti.append(Cliente(c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8],c[9]))  
    return clienti
  
  def get_cliente(self, cod):
    cur = self.mysql.connection.cursor()
    cur.execute('select cod, RagSoc, Ind, cap, citta, piva, cfisc, old_cod, tel, email from clienti where cod={}'.format(cod))
    c = cur.fetchone()
    return Cliente(c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8],c[9])

  def crea_cliente(self, ragione_sociale, indirizzo, cap, citta, p_iva, cod_fiscale, telefono, e_mail):
    conn = self.mysql.connection
    cur = conn.cursor()
    cur.execute('select max(cod) from clienti')
    last_id = cur.fetchone()[0]
    sql = '''insert into clienti (cod, RagSoc, Ind, cap, citta, piva, cfisc, tel, email) values ({}, '{}','{}','{}','{}','{}','{}','{}','{}') '''.format(last_id + 1,ragione_sociale, indirizzo, cap, citta, p_iva, cod_fiscale, telefono, e_mail)
    rows = cur.execute(sql)
    conn.commit()
    return rows
  
  def modifica_cliente(self, codice, ragione_sociale, indirizzo, cap, citta, p_iva, cod_fiscale, telefono, e_mail):
    conn = self.mysql.connection
    cur = conn.cursor()
    sql = '''update clienti set RagSoc='{}', Ind='{}', cap='{}', citta='{}', piva='{}', cfisc='{}', tel='{}', email='{}' where cod={}'''.format(ragione_sociale, indirizzo, cap, citta, p_iva, cod_fiscale, telefono, e_mail, codice)
    rows = cur.execute(sql)
    conn.commit()
    return rows

class Utente(object):
  def __init__(self, id, nome, username, profilo, attivo):
    self.id = id
    self.nome = nome
    self.username = username
    self.profilo = profilo
    self.is_active = attivo
    self.is_authenticated = False
    self.is_anonymous = False
    
  def __repr__(self):
    return self.username
  
  def get_id(self):
    return unicode(id)
  
class Azienda(object):
  def __init__(self, id, Ragione_Sociale, Descr, PI, CF, Indirizzo, Citta, CAP, Provincia, Telefono, MF, Fax, E_mail):
    self.id = id
    self.ragione_sociale = Ragione_Sociale
    self.descrizione = Descr
    self.p_iva = PI
    self.cod_fiscale = CF
    self.indirizzo = Indirizzo
    self.citta = Citta
    self.cap = CAP
    self.provincia = Provincia
    self.telefono = Telefono
    self.misuratore_fiscale = MF # il logotipo presente sugli scontrini
    self.fax = Fax
    self.e_mail = E_mail
    
  def __repr__(self):
    return self.ragione_sociale
    
    
class Cliente(object):
  def __init__(self, cod, RagSoc, Ind, cap, citta, piva, cfisc, old_cod, tel, email):
    self.codice = cod
    self.ragione_sociale = RagSoc
    self.indirizzo = Ind
    self.cap = cap
    self.citta = citta
    self.p_iva = piva
    self.cod_fiscale = cfisc
    self.old_cod = old_cod
    self.telefono = tel
    self.email = email
  
  def __repr__(self):
    return self.ragione_sociale
    
    
    
    
    
    
    
    