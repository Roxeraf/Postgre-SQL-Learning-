-- PostgreSQL-Lernapp: isoliertes Schema learn
-- Deterministisch, resetbar. Kein produktives Fremdschema.

DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lernuser') THEN
      CREATE ROLE lernuser LOGIN PASSWORD 'lernuser';
   END IF;
END
$$;

DROP SCHEMA IF EXISTS learn CASCADE;
CREATE SCHEMA learn;

CREATE TABLE learn.clients (
    id       integer PRIMARY KEY,
    name     text NOT NULL,
    country  text NOT NULL
);

CREATE TABLE learn.orders (
    id            integer PRIMARY KEY,
    order_number  integer NOT NULL,
    client_id     integer REFERENCES learn.clients(id),
    client        text,
    status        text NOT NULL,
    quantity      integer,
    note          text,
    created_at    date NOT NULL
);

CREATE TABLE learn.stock (
    id        integer PRIMARY KEY,
    item      text NOT NULL,
    quantity  integer,
    weight    integer
);

CREATE TABLE learn.order_items (
    id        integer PRIMARY KEY,
    order_id  integer REFERENCES learn.orders(id),
    sku       text NOT NULL,
    qty       integer NOT NULL
);

INSERT INTO learn.clients (id, name, country) VALUES
    (10, 'Helio',    'AT'),
    (20, 'Alpin',    'DE'),
    (30, 'Nordkai',  'CH'),
    (40, 'Westfeld', 'DE');

INSERT INTO learn.orders (id, order_number, client_id, client, status, quantity, note, created_at) VALUES
    (1,  4711, 10,   'Helio',   'offen',     12,   'eilig',           '2026-09-08'),
    (2,  4712, 20,   'Alpin',   'fertig',     4,   NULL,              '2026-09-07'),
    (3,  4713, 10,   'Helio',   'offen',     25,   NULL,              '2026-09-09'),
    (4,  4714, 20,   'Alpin',   'offen',      8,   'telefonisch',     '2026-09-06'),
    (5,  4715, 10,   'Helio',   'fertig',    30,   NULL,              '2026-09-05'),
    (6,  4716, 30,   'Nordkai', 'offen',     15,   NULL,              '2026-09-10'),
    (7,  4717, 20,   'Alpin',   'storniert',  2,   NULL,              '2026-09-04'),
    (8,  4718, 10,   'Helio',   'offen',     50,   'eilig',           '2026-09-10'),
    (9,  4719, 10,   'Helio',   'offen',     18,   NULL,              '2026-09-11'),
    (10, 4720, 20,   'Alpin',   'fertig',    22,   NULL,              '2026-09-03'),
    (11, 4721, 30,   'Nordkai', 'fertig',     9,   NULL,              '2026-09-02'),
    (12, 4722, 30,   'Nordkai', 'offen',      6,   NULL,              '2026-09-12'),
    (13, 4723, 10,   'Helio',   'storniert', 11,   NULL,              '2026-09-01'),
    (14, 4724, 20,   'Alpin',   'offen',     40,   'eilig',           '2026-09-13'),
    (15, 4725, 30,   'Nordkai', 'offen',      3,   NULL,              '2026-09-08'),
    (16, 4726, 10,   'Helio',   'fertig',     7,   NULL,              '2026-09-14'),
    (17, 4727, 20,   'Alpin',   'offen',     16,   NULL,              '2026-09-15'),
    (18, 4728, 30,   'Nordkai', 'storniert',  5,   NULL,              '2026-09-06'),
    (19, 4729, 10,   'Helio',   'offen',    100,   'große Menge',     '2026-09-16'),
    (20, 4730, NULL, NULL,      'offen',     14,   NULL,              '2026-09-09'),
    (21, 4731, 20,   'Alpin',   'offen',    NULL,  NULL,              '2026-09-11'),
    (22, 4732, 10,   'Helio',   'fertig',   NULL,  'Menge folgt',     '2026-09-07'),
    (23, 4733, 30,   'Nordkai', 'offen',      1,   NULL,              '2026-09-17'),
    (24, 4734, 10,   'Helio',   'offen',     13,   NULL,              '2026-09-18');

INSERT INTO learn.stock (id, item, quantity, weight) VALUES
    (1, 'Palette A', 40,   120),
    (2, 'Palette B',  8,    80),
    (3, 'Karton C',  15,    25),
    (4, 'Palette D',  3,   100),
    (5, 'Karton E',  NULL,  40),
    (6, 'Folie F',   12,  NULL),
    (7, 'Palette G',  0,    50);

INSERT INTO learn.order_items (id, order_id, sku, qty) VALUES
    (1,  1,  'Palette A', 2),
    (2,  1,  'Karton C',  4),
    (3,  2,  'Palette B', 1),
    (4,  3,  'Palette A', 5),
    (5,  3,  'Folie F',   2),
    (6,  4,  'Karton C',  3),
    (7,  5,  'Palette D', 1),
    (8,  6,  'Palette A', 1),
    (9,  6,  'Palette B', 1),
    (10, 7,  'Karton E',  2),
    (11, 8,  'Palette A', 10),
    (12, 9,  'Karton C',  6),
    (13, 10, 'Palette D', 2),
    (14, 11, 'Folie F',   1),
    (15, 12, 'Karton C',  2),
    (16, 13, 'Palette B', 1),
    (17, 14, 'Palette A', 8),
    (18, 14, 'Karton C',  3),
    (19, 15, 'Folie F',   4),
    (20, 16, 'Palette G', 1),
    (21, 17, 'Palette A', 2),
    (22, 18, 'Karton C',  1),
    (23, 19, 'Palette A', 20),
    (24, 21, 'Folie F',   3),
    (25, 22, 'Palette D', 1),
    (26, 23, 'Karton C',  1),
    (27, 24, 'Palette A', 1),
    (28, 24, 'Folie F',   2);

GRANT USAGE ON SCHEMA learn TO lernuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA learn TO lernuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA learn GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lernuser;

ALTER ROLE lernuser SET statement_timeout = '5s';
ALTER ROLE lernuser SET search_path TO learn, public;
