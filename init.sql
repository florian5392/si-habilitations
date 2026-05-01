CREATE TABLE etablissements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(255) NOT NULL,
  UNIQUE KEY uk_etab_nom (nom)
);

CREATE TABLE applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(255) NOT NULL,
  editeur VARCHAR(255),
  domaine VARCHAR(255),
  id_etablissement INT,
  FOREIGN KEY (id_etablissement) REFERENCES etablissements(id) ON DELETE CASCADE,
  UNIQUE KEY uk_app_nom_etab (nom, id_etablissement)
);

CREATE TABLE profils (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_application INT NOT NULL,
  nom VARCHAR(255) NOT NULL,
  description TEXT,
  FOREIGN KEY (id_application) REFERENCES applications(id) ON DELETE CASCADE,
  UNIQUE KEY uk_profil_nom_app (nom, id_application)
);

CREATE TABLE droits (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_application INT NOT NULL,
  nom VARCHAR(255) NOT NULL,
  description TEXT,
  type_valeur ENUM('booleen','liste') DEFAULT 'booleen',
  FOREIGN KEY (id_application) REFERENCES applications(id) ON DELETE CASCADE,
  UNIQUE KEY uk_droit_nom_app (nom, id_application)
);

CREATE TABLE valeurs_liste (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_droit INT NOT NULL,
  valeur VARCHAR(255) NOT NULL,
  ordre INT DEFAULT 0,
  FOREIGN KEY (id_droit) REFERENCES droits(id) ON DELETE CASCADE,
  UNIQUE KEY uk_val_droit (id_droit, valeur)
);

CREATE TABLE habilitations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_profil INT NOT NULL,
  id_droit INT NOT NULL,
  valeur VARCHAR(255),
  FOREIGN KEY (id_profil) REFERENCES profils(id) ON DELETE CASCADE,
  FOREIGN KEY (id_droit) REFERENCES droits(id) ON DELETE CASCADE,
  UNIQUE KEY uk_hab_profil_droit (id_profil, id_droit)
);

CREATE TABLE audit_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  utilisateur VARCHAR(255),
  action ENUM('INSERT','UPDATE','DELETE') NOT NULL,
  table_name VARCHAR(100) NOT NULL,
  record_id INT,
  champ VARCHAR(255),
  ancienne_valeur TEXT,
  nouvelle_valeur TEXT,
  INDEX idx_audit_created (created_at),
  INDEX idx_audit_table (table_name)
);
