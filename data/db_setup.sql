CREATE TABLE maestros (
    maestroid INTEGER PRIMARY KEY NOT NULL, 
    nombre TEXT NOT NULL
    );

CREATE TABLE eventos (
    eventoid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    tipo TEXT NOT NULL,
    salon TEXT NOT NULL,
    tiempo TEXT NOT NULL,
    unix INTEGER NOT NULL,
    maestro INTEGER, 
    FOREIGN KEY(Maestro) REFERENCES maestros(maestroid)
    );
