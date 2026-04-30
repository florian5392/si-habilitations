CREATE TABLE etablissements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(255) NOT NULL
);

CREATE TABLE applications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(255) NOT NULL,
  editeur VARCHAR(255),
  domaine VARCHAR(255),
  id_etablissement INT,
  FOREIGN KEY (id_etablissement) REFERENCES etablissements(id)
);

CREATE TABLE profils (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_application INT NOT NULL,
  nom VARCHAR(255) NOT NULL,
  description TEXT,
  FOREIGN KEY (id_application) REFERENCES applications(id)
);

CREATE TABLE droits (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_application INT NOT NULL,
  nom VARCHAR(255) NOT NULL,
  description TEXT,
  type_valeur ENUM('booleen','liste') DEFAULT 'booleen',
  FOREIGN KEY (id_application) REFERENCES applications(id)
);

CREATE TABLE valeurs_liste (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_droit INT NOT NULL,
  valeur VARCHAR(255) NOT NULL,
  ordre INT DEFAULT 0,
  FOREIGN KEY (id_droit) REFERENCES droits(id)
);

CREATE TABLE habilitations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_profil INT NOT NULL,
  id_droit INT NOT NULL,
  valeur VARCHAR(255),
  FOREIGN KEY (id_profil) REFERENCES profils(id),
  FOREIGN KEY (id_droit) REFERENCES droits(id)
);
