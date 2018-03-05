alter table macdonald.fattura add column ragsoc     varchar(120)    after cliente_id;
alter table macdonald.fattura add column p_iva	    varchar(20)     after ragsoc;
alter table macdonald.fattura add column cod_fisc	varchar(20)     after p_iva;
alter table macdonald.fattura add column indirizzo  varchar(120)    after cod_fisc;
alter TABLE macdonald.fattura add column citta      varchar(120)    after indirizzo;
alter TABLE macdonald.fattura add COLUMN cap        VARCHAR(10)     after citta;
alter TABLE macdonald.fattura add COLUMN prov       VARCHAR(2)      after cap;
alter TABLE macdonald.fattura add COLUMN tel        VARCHAR(50)     after prov;
alter TABLE macdonald.fattura add COLUMN fax        VARCHAR(20)     after tel;
alter TABLE macdonald.fattura add COLUMN email      VARCHAR(120)    after fax;


UPDATE fattura f JOIN cliente c ON (f.cliente_id = c.id)
SET f.ragsoc = c.ragsoc,
	f.p_iva = c.p_iva,
	f.cod_fisc = c.cod_fisc,
	f.indirizzo = c.indirizzo,
	f.citta = c.citta,
	f.cap = c.cap,
	f.prov = c.prov,
	f.tel = c.tel,
	f.fax = c.fax,
	f.email = c.email
WHERE f.id > 1;
