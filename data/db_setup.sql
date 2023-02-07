CREATE TABLE maestros (
    maestroid INTEGER PRIMARY KEY NOT NULL, 
    nombre TEXT NOT NULL
    );

CREATE TABLE eventos (
    eventoid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    tipo TEXT NOT NULL,
    salon TEXT NOT NULL,
    tiempo TEXT NOT NULL,
    maestro INTEGER, 
    FOREIGN KEY(Maestro) REFERENCES maestros(maestroid)
    );

INSERT INTO maestros(maestroid, nombre)
VALUES (1, 'Julian');

INSERT INTO eventos(tipo, salon, tiempo, maestro)
VALUES ('TEST1', '1', strftime('%Y-%m-%d %H:%M'), 1);

INSERT INTO eventos(tipo, salon, tiempo)
VALUES ('TEST2', '2', strftime('%Y-%m-%d %H:%M'));