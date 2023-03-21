CREATE TABLE maestros (
    id INTEGER PRIMARY KEY NOT NULL,
    nombre TEXT NOT NULL,
    file_url TEXT NOT NULL
    );

CREATE TABLE eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    tipo TEXT NOT NULL,
    salon TEXT NOT NULL,
    tiempo TEXT NOT NULL,
    unix INTEGER NOT NULL,
    maestro INTEGER, 
    FOREIGN KEY(maestro) REFERENCES maestros(id)
    FOREIGN KEY(salon) REFERENCES salones(id)
    );

CREATE TABLE salones (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    nombre TEXT NOT NULL
    );
