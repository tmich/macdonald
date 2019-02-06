from xml.etree.ElementTree import Element, SubElement, Comment, tostring
import lxml.etree as etree

'''https://www.fatturapa.gov.it/export/fatturazione/sdi/fatturapa/v1.2/Rappresentazione_tabellare_del_tracciato_FatturaPA_versione_1.2.pdf'''

class NodoFPR(object):
	def __init__(self, nome='', testo='', attrs=dict()):
		if nome != '':
			self.elem = Element(nome, attrs)
			if testo != '':
				self.elem.text = testo
		else:
			self.elem = None
		
	def to_element(self):
		return self.elem
		
	def append(self, element):
		self.elem.append(element.to_element())
		return element
		
	def __repr__(self):
		return tostring(self.elem, encoding="utf8")


''' Fattura Elettronica Formato FPR12 '''
class FPR12(NodoFPR):
	def __init__(self): 
		super(FPR12, self).__init__("p:FatturaElettronica", 
						 attrs={'xmlns:p'   : 'http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2',
						 'xmlns:xsi' : 'http://www.w3.org/2001/XMLSchema-instance',
						 'versione'  : "FPR12"})
		self.header = self.append(FatturaElettronicaHeader())
		self.body = self.append(FatturaElettronicaBody())


class FatturaElettronicaHeader(NodoFPR):
	def __init__(self):
		super(FatturaElettronicaHeader, self).__init__("FatturaElettronicaHeader")

		
class DatiTrasmissione(NodoFPR):
	def __init__(self):
		super(DatiTrasmissione, self).__init__("DatiTrasmissione")


class IdTrasmittente(NodoFPR):
	def __init__(self, IdPaese, IdCodice):
		super(IdTrasmittente, self).__init__("IdTrasmittente")
		idPaese = SubElement(self.elem, "IdPaese")
		idPaese.text = IdPaese
		idCodice = SubElement(self.elem, "IdCodice")
		idCodice.text = IdCodice


class IdFiscaleIVA(NodoFPR):
	def __init__(self, IdPaese, IdCodice):
		super(IdFiscaleIVA, self).__init__("IdFiscaleIVA")
		idPaese = SubElement(self.elem, "IdPaese")
		idPaese.text = IdPaese
		idCodice = SubElement(self.elem, "IdCodice")
		idCodice.text = IdCodice


class Anagrafica(NodoFPR):
	def __init__(self, denominazione='', nome='', cognome='', titolo='', codEORI=''):
		super(Anagrafica, self).__init__("Anagrafica") 
		if denominazione != '':
			self.append(NodoFPR("Denominazione", denominazione))
		if nome != '':
			self.append(NodoFPR("Nome", nome))
		if cognome != '':
			self.append(NodoFPR("Cognome", cognome))
		if titolo != '':
			self.append(NodoFPR("Titolo", titolo))
		if codEORI != '':
			self.append(NodoFPR("CodEORI", codEORI))
	
  
class Sede(NodoFPR):
	def __init__(self, indirizzo='', numeroCivico='', cap='', comune='', provincia='', nazione=''):
		super(Sede, self).__init__("Sede")
		if indirizzo != '':
			self.append(NodoFPR("Indirizzo", indirizzo))
		if numeroCivico != '':
			self.append(NodoFPR("NumeroCivico", numeroCivico))
		if cap != '':
			self.append(NodoFPR("CAP", cap))
		if comune != '':
			self.append(NodoFPR("Comune", comune))
		if provincia != None:
			if provincia != '':
				self.append(NodoFPR("Provincia", provincia))
		if nazione != '':
			self.append(NodoFPR("Nazione", nazione))


# 2
class FatturaElettronicaBody(NodoFPR):
	def __init__(self):
		super(FatturaElettronicaBody, self).__init__("FatturaElettronicaBody")
		self.dati_generali = self.append(DatiGenerali())
		self.dati_beni_servizi = self.append(DatiBeniServizi())


# 2.1
class DatiGenerali(NodoFPR):
	def __init__(self):
		super(DatiGenerali, self).__init__("DatiGenerali")
		#self.documento = self.append(DatiGeneraliDocumento())
		

# 2.1.1
class DatiGeneraliDocumento(NodoFPR):
	def __init__(self, tipo_documento, divisa, data, numero):
		super(DatiGeneraliDocumento, self).__init__("DatiGeneraliDocumento")
		self.append(TipoDocumento(tipo_documento))
		self.append(Divisa(divisa))
		self.append(Data(data))
		self.append(Numero(numero))
		# self.dati_ritenuta = self.append(DatiRitenuta())
		# self.dati_bollo = self.append(DatiBollo())


# 2.1.1.1
class TipoDocumento(NodoFPR):
	def __init__(self, tipo_documento):
		super(TipoDocumento, self).__init__("TipoDocumento", tipo_documento)


# 2.1.1.2
class Divisa(NodoFPR):
	def __init__(self, divisa):
		super(Divisa, self).__init__("Divisa", divisa)


# 2.1.1.3
class Data(NodoFPR):
	def __init__(self, data):
		super(Data, self).__init__("Data", data)
		

# 2.1.1.4
class Numero(NodoFPR):
	def __init__(self, numero):
		super(Numero, self).__init__("Numero", numero)  
		

# 2.1.1.5
class DatiRitenuta(NodoFPR):
	def __init__(self):
		super(DatiRitenuta, self).__init__("DatiRitenuta")
		self.tipo = self.append(TipoRitenuta())
		self.importo = self.append(ImportoRitenuta())
		self.aliquota = self.append(AliquotaRitenuta())
		self.causale_pagamento = self.append(CausalePagamento())
		

# 2.1.1.5.1
class TipoRitenuta(NodoFPR):
	def __init__(self):
		super(TipoRitenuta, self).__init__("TipoRitenuta")     
		

# 2.1.1.5.2
class ImportoRitenuta(NodoFPR):
	def __init__(self):
		super(ImportoRitenuta, self).__init__("ImportoRitenuta")
		
		
# 2.1.1.5.3
class AliquotaRitenuta(NodoFPR):
	def __init__(self):
		super(AliquotaRitenuta, self).__init__("AliquotaRitenuta")  

		
# 2.1.1.5.4
class CausalePagamento(NodoFPR):
	def __init__(self):
		super(CausalePagamento, self).__init__("CausalePagamento") 

  
# 2.1.1.6
class DatiBollo(NodoFPR):
	def __init__(self):
		super(DatiBollo, self).__init__("DatiBollo") 
		
		
	 
# 2.2 
class DatiBeniServizi(NodoFPR):
	def __init__(self):
		super(DatiBeniServizi, self).__init__("DatiBeniServizi") 
		self.dettaglio_linee = []
		self.dati_riepilogo = []

 
# 2.2.1 
class DettaglioLinee(NodoFPR):
	def __init__(self, numero_linea, descrizione, prezzo_unitario, prezzo_totale, aliquota_iva, unita_misura=None, qta=None):
		super(DettaglioLinee, self).__init__("DettaglioLinee")
		self.append(NumeroLinea(numero_linea))
		self.append(Descrizione(descrizione))
		if qta:
			self.append(Quantita(qta))
		self.append(PrezzoUnitario(prezzo_unitario))
		self.append(PrezzoTotale(prezzo_totale))
		self.append(AliquotaIVA(aliquota_iva))
		if unita_misura:
			self.append(UnitaMisura(unita_misura))

# 2.2.1.1 
class NumeroLinea(NodoFPR):
	def __init__(self, num):
		super(NumeroLinea, self).__init__("NumeroLinea", '{:d}'.format(num))
		

# 2.2.1.4
class Descrizione(NodoFPR):
	def __init__(self, descrizione):
		super(Descrizione, self).__init__("Descrizione", str(descrizione))
		

# 2.2.1.5
class Quantita(NodoFPR):
	def __init__(self, qta):
		super(Quantita, self).__init__("Quantita", '{:.2f}'.format(qta))
 
# 2.2.1.6 
class UnitaMisura(NodoFPR):
	def __init__(self, unita_misura):
		super(UnitaMisura, self).__init__("UnitaMisura", str(unita_misura))

 
# 2.2.1.9
class PrezzoUnitario(NodoFPR):
	def __init__(self, prezzo_unitario):
		super(PrezzoUnitario, self).__init__("PrezzoUnitario", '{:.4f}'.format(prezzo_unitario))



# 2.2.1.11
class PrezzoTotale(NodoFPR):
	def __init__(self, prezzo_totale):
		super(PrezzoTotale, self).__init__("PrezzoTotale", '{:.4f}'.format(prezzo_totale))
  

# 2.2.1.12
class AliquotaIVA(NodoFPR):
	def __init__(self, aliquota_iva):
		super(AliquotaIVA, self).__init__("AliquotaIVA", '{:.2f}'.format(aliquota_iva))
  
  
# 2.2.2  
class DatiRiepilogo(NodoFPR):
	def __init__(self, aliquota_iva, imponibile, imposta, esigibilita=None):
		super(DatiRiepilogo, self).__init__("DatiRiepilogo")
		self.append(AliquotaIVA(aliquota_iva))
		self.append(ImponibileImporto(imponibile))
		self.append(Imposta(imposta))
		if esigibilita:
			self.append(EsigibilitaIVA(esigibilita))
  

# 2.2.2.5
class ImponibileImporto(NodoFPR):
	def __init__(self, imponibile):
		super(ImponibileImporto, self).__init__("ImponibileImporto", '{:.2f}'.format(imponibile)) 
  
  

# 2.2.2.5
class Imposta(NodoFPR):
	def __init__(self, imposta):
		super(Imposta, self).__init__("Imposta", '{:.2f}'.format(imposta)) 
		
		
# 2.2.2.7 
class EsigibilitaIVA(NodoFPR):
	def __init__(self, esigibilita):
		super(EsigibilitaIVA, self).__init__("EsigibilitaIVA", str(esigibilita)) 



def converti_fattura(ft, progr):
	f = FPR12()
		
	# 1.1 Dati Trasmissione
	dt = DatiTrasmissione()
	dt.append(IdTrasmittente("IT", ft.azienda.p_iva))
	dt.append(NodoFPR("ProgressivoInvio", str(progr)))
	dt.append(NodoFPR("FormatoTrasmissione", "FPR12"))
	if ft.cliente.cod_destinatario != None and ft.cliente.cod_destinatario != '':
		dt.append(NodoFPR("CodiceDestinatario", ft.cliente.cod_destinatario))
	else:
		dt.append(NodoFPR("CodiceDestinatario", '0000000'))
		if ft.cliente.pec != None and ft.cliente.pec.strip() != '':
			dt.append(NodoFPR("PECDestinatario", ft.cliente.pec))
	f.header.append(dt)

	# 1.2 CedentePrestatore
	ced = NodoFPR("CedentePrestatore")

	# 1.2.1 DatiAnagrafici
	dan = NodoFPR("DatiAnagrafici")
	dan.append(IdFiscaleIVA("IT", ft.azienda.p_iva))
	dan.append(NodoFPR("CodiceFiscale", ft.azienda.cod_fisc))
	dan.append(Anagrafica(ft.azienda.ragsoc))
	dan.append(NodoFPR("RegimeFiscale", ft.azienda.regime_fiscale))
	ced.append(dan)

	# 1.2.2 Sede
	ced.append(Sede(ft.azienda.indirizzo, "", ft.azienda.cap, ft.azienda.citta, ft.azienda.prov, "IT"))
	f.header.append(ced)

	# 1.4 CessionarioCommittente
	cc = NodoFPR("CessionarioCommittente")

	# 1.4.1 DatiAnagrafici
	danag = NodoFPR("DatiAnagrafici")
	danag.append(IdFiscaleIVA("IT", ft.cliente.p_iva))
	if ft.cliente.cod_fisc != None:
		if ft.cliente.cod_fisc.strip() != '':
			danag.append(NodoFPR("CodiceFiscale", ft.cliente.cod_fisc))
	danag.append(Anagrafica(ft.cliente.ragsoc))
	cc.append(danag)

	# 1.4.2 Sede
	cc.append(Sede(ft.cliente.indirizzo, "", ft.cliente.cap, ft.cliente.citta, ft.cliente.prov, "IT"))
	f.header.append(cc)

	# 2.1.1 Dati Generali Documento
	f.body.dati_generali.append(DatiGeneraliDocumento("TD01", "EUR", ft.data.isoformat(), str(ft.data.year) + "/" + str(ft.num)))

	# 2.2.1 DettaglioLinee
	n = 1
	for v in ft.voci:
		f.body.dati_beni_servizi.append(DettaglioLinee(n, v.descr, float(v.imponibile_unitario_nr()), 
			float(v.imponibile_nr()), float(v.aliq), qta=float(v.qta)))
		n = n + 1

	# 2.2.2 DatiRiepilogo
	f.body.dati_beni_servizi.append(DatiRiepilogo(22.0, float(ft.imponibile_nr()), float(ft.iva_nr()), esigibilita='I'))

	root = etree.fromstring(str(f))
	xml = etree.tostring(root, pretty_print=True, encoding="utf8")
	#print(xml)
	return xml
