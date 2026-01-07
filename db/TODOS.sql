 CREATE TABLE Nutzer (
    nutzer_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(250) NOT NULL UNIQUE,
    password VARCHAR(250) NOT NULL
); 

CREATE TABLE Mitarbeiter (
    mitarbeiter_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    rolle VARCHAR(20)
);   

CREATE TABLE Raumtyp (
    raumtyp_id INT AUTO_INCREMENT PRIMARY KEY,
    bezeichnung VARCHAR(40) NOT NULL,
    beschreibung VARCHAR(100)
);

CREATE TABLE todos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nutzer_id INT NOT NULL,
    content VARCHAR(100),
    due DATETIME,
    FOREIGN KEY (nutzer_id) REFERENCES Nutzer(nutzer_id)
);


CREATE TABLE Zimmer (
    zimmer_id INT AUTO_INCREMENT PRIMARY KEY,
    zimmernummer VARCHAR(10) NOT NULL,
    stockwerk INT NOT NULL,
    kapazitaet INT NOT NULL,
    raumtyp_id INT NOT NULL,
    FOREIGN KEY (raumtyp_id) REFERENCES Raumtyp(raumtyp_id)
);

CREATE TABLE Buchung (
    buchung_id INT AUTO_INCREMENT PRIMARY KEY,
    startdatum DATE NOT NULL,
    enddatum DATE NOT NULL,  
    zeit TIME,
    zimmer_id INT NOT NULL,
    nutzer_id INT NOT NULL,
    mitarbeiter_id INT,
    FOREIGN KEY (nutzer_id) REFERENCES Nutzer(nutzer_id),
    FOREIGN KEY (zimmer_id) REFERENCES Zimmer(zimmer_id),
    FOREIGN KEY (mitarbeiter_id) REFERENCES Mitarbeiter(mitarbeiter_id)
);

CREATE TABLE Zahlung (
    zahlung_id INT AUTO_INCREMENT PRIMARY KEY,
    betrag DECIMAL(10,2) NOT NULL,
    zahlungsdatum DATE NOT NULL,
    zahlungsart VARCHAR(100) NOT NULL,
    buchung_id INT NOT NULL,
    FOREIGN KEY (buchung_id) REFERENCES Buchung(buchung_id)
);

CREATE TABLE Login_Historie (
    login_id INT AUTO_INCREMENT PRIMARY KEY,
    nutzer_id INT NOT NULL,
    loginzeit DATETIME,
    logoutzeit DATETIME,
    FOREIGN KEY (nutzer_id) REFERENCES Nutzer(nutzer_id)
);




INSERT INTO Nutzer (username, password) VALUES
('max.mustermann', 'mm1'),
('anna.schmidt', 'as4'),
('luca.meier', 'lm2');

INSERT INTO Mitarbeiter (name, email, rolle) VALUES
('Peter Müller', 'p.mueller@hotel.de', 'Admin'),
('Lisa Weber', 'l.weber@hotel.de', 'Rezeption'),
('Tom Becker', 't.becker@hotel.de', 'Service');

INSERT INTO Raumtyp (bezeichnung, beschreibung) VALUES
('Einzelzimmer', 'Zimmer für eine Person'),
('Doppelzimmer', 'Zimmer für zwei Personen'),
('Suite', 'Luxuszimmer mit Wohnzimmer');

INSERT INTO todos (nutzer_id, content, due) VALUES
(1, 'Rechnung prüfen', '2026-01-10 12:00:00'),
(1, 'Zimmer reservieren', '2026-01-15 18:00:00'),
(2, 'Urlaub planen', '2026-02-01 20:00:00');

INSERT INTO Zimmer (zimmernummer, stockwerk, kapazitaet, raumtyp_id) VALUES
('101', 1, 1, 1),
('202', 2, 2, 2),
('301', 3, 4, 3);

INSERT INTO Buchung (startdatum, enddatum, zeit, zimmer_id, nutzer_id, mitarbeiter_id) VALUES
('2026-02-01', '2026-02-05', '14:00:00', 1, 1, 2),
('2026-03-10', '2026-03-12', '16:00:00', 2, 2, 1),
('2026-04-01', '2026-04-07', '15:00:00', 3, 3, 3);

INSERT INTO Zahlung (betrag, zahlungsdatum, zahlungsart, buchung_id) VALUES
(399.99, '2026-01-25', 'Kreditkarte', 1),
(199.99, '2026-03-01', 'PayPal', 2),
(899.99, '2026-03-20', 'Überweisung', 3);

INSERT INTO Login_Historie (nutzer_id, loginzeit, logoutzeit) VALUES
(1, '2026-01-01 10:15:00', '2026-01-01 11:00:00'),
(2, '2026-01-02 18:30:00', '2026-01-02 19:10:00'),
(3, '2026-01-03 09:00:00', '2026-01-03 09:45:00');

 