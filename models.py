# models.py

class Db(object):
  def __init__(self, mysql):
    self.mysql = mysql
    
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
    cur.execute('''select cod, RagSoc, Ind, cap, citta, piva, cfisc, old_cod, tel, email from clienti limit {}, {}'''.format(offset, count))
    for c in cur.fetchall():
      clienti.append(Cliente(c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8],c[9]))  
    return clienti
  
  def get_cliente(self, cod):
    cur = self.mysql.connection.cursor()
    cur.execute('select cod, RagSoc, Ind, cap, citta, piva, cfisc, old_cod, tel, email from clienti where cod={}'.format(cod))
    c = cur.fetchone()
    return Cliente(c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8],c[9])


class Utente(object):
  def __init__(self, id, nome, username, profilo, attivo):
    self.id = id
    self.nome = nome
    self.username = username
    self.profilo = profilo
    self.attivo = attivo
    
  def __repr__(self):
    return self.username
  
  
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
    
    
    
    
    
    
    
    