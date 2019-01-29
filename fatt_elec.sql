CREATE TABLE `invio_fattura_elettronica` (
	`id` INT(11) NOT NULL AUTO_INCREMENT,
	`fattura_id` INT(11) NOT NULL,
	`data_invio` DATE NULL DEFAULT NULL,
	`xml` TEXT NULL DEFAULT NULL,
	`esito` VARCHAR(2) NULL DEFAULT NULL,
	`errore` VARCHAR(200) NULL DEFAULT NULL,
	PRIMARY KEY (`id`),
	INDEX `fattura_id` (`fattura_id`),
	CONSTRAINT `invio_fattura_elettronica_ibfk_1` FOREIGN KEY (`fattura_id`) REFERENCES `fattura` (`id`)
)
COLLATE='latin1_swedish_ci'
ENGINE=InnoDB
;

ALTER TABLE cliente
	ADD COLUMN pec VARCHAR(120) NULL DEFAULT NULL AFTER email,
	ADD COLUMN cod_destinatario VARCHAR(50) NULL DEFAULT NULL AFTER pec;

ALTER TABLE anagrafica
	ADD COLUMN cod_destinatario VARCHAR(50) NULL DEFAULT NULL AFTER email,		-- M5UXCR1
	ADD COLUMN regime_fiscale VARCHAR(4) NULL DEFAULT NULL AFTER cod_destinatario;	-- RF01