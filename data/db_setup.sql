CREATE TABLE Maestros (
    maestroid INTEGER PRIMARY KEY NOT NULL, 
    Nombre TEXT NOT NULL
    );

CREATE TABLE Eventos (
    eventoid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    Salon TEXT NOT NULL,
    Tiempo TEXT NOT NULL,
    Maestro INTEGER NOT NULL, 
    FOREIGN KEY(Maestro) REFERENCES Maestros(maestroid)
    );

INSERT INTO Maestros (maestroid, Nombre)
VALUES (1, 'Julian');

INSERT INTO Eventos (Salon, Tiempo, Maestro)
VALUES ('EJEMPLO', date('now'), 1);