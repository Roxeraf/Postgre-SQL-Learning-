-- ============================================================
-- FlowApp/WMX Lern-Datenbank
-- Vereinfachtes, aber strukturell realistisches Abbild der
-- Instanz "instance_1" / Schema-Präfix "flowapp_demo_"
-- Wissensbasis: PostgreSQL_FlowApp_Einarbeitung.docx (Teile A–P)
-- ============================================================

CREATE SCHEMA IF NOT EXISTS instance_1;
CREATE SCHEMA IF NOT EXISTS subscription;

-- ------------------------------------------------------------
-- Stammdaten / Mandanten
-- ------------------------------------------------------------
CREATE TABLE instance_1.flowapp_demo_client (
    id                              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                            varchar NOT NULL,
    alias                           varchar NOT NULL,
    name                            jsonb NOT NULL,
    accounting_area_item_master_id  uuid UNIQUE
);

CREATE TABLE instance_1.flowapp_demo_quantity_unit (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_item_category (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    designation   jsonb NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_item_master (
    id                              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id                       uuid REFERENCES instance_1.flowapp_demo_client(accounting_area_item_master_id),
    designation_a                   jsonb NOT NULL,
    item_group                      varchar,
    cat_item_group_id               uuid REFERENCES instance_1.flowapp_demo_item_category(id),
    quantity_unit_id                uuid REFERENCES instance_1.flowapp_demo_quantity_unit(id),
    customs_tariff_number_taric     varchar
);

CREATE TABLE instance_1.flowapp_demo_order_class (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL,
    name   jsonb NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_country_code (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    iso_code  varchar NOT NULL,
    name      jsonb NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_incoterm (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL,
    name   varchar NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_customs_status_profile (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL,
    name   jsonb NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_customs_procedure_profile (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL,
    name   jsonb NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_address_category (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL,
    name   jsonb NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_bundling_unit (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_handling_unit_class (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_handling_unit_identification_type (
    id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alias  varchar NOT NULL
);

-- ------------------------------------------------------------
-- Aufträge
-- ------------------------------------------------------------
CREATE TABLE instance_1.flowapp_demo_order_head (
    id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id                 integer NOT NULL,
    order_number             varchar NOT NULL,
    client_id                uuid REFERENCES instance_1.flowapp_demo_client(id),
    order_class_id           uuid REFERENCES instance_1.flowapp_demo_order_class(id),
    task_status              varchar NOT NULL DEFAULT '10',
    putaway_status           varchar DEFAULT '00',
    loading_status           varchar DEFAULT '00',
    packaging_status         varchar DEFAULT '00',
    reservation_status       varchar DEFAULT '00',
    allocation_status        varchar DEFAULT '00',
    shipment_number          varchar,
    planned_processing_date  timestamp,
    confirmed_end_date_time  timestamptz,
    created_date             timestamptz NOT NULL DEFAULT now(),
    customs_procedures_id    uuid REFERENCES instance_1.flowapp_demo_customs_procedure_profile(id),
    incoterms_id             uuid REFERENCES instance_1.flowapp_demo_incoterm(id)
);

CREATE TABLE instance_1.flowapp_demo_order_position (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_head_id  uuid REFERENCES instance_1.flowapp_demo_order_head(id),
    item_master_id uuid REFERENCES instance_1.flowapp_demo_item_master(id),
    quantity       integer NOT NULL DEFAULT 1
);

CREATE TABLE instance_1.flowapp_demo_order_position_reference (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_position_id  uuid REFERENCES instance_1.flowapp_demo_order_position(id),
    reference_key      varchar,
    reference_value    varchar,
    source_slug_name   varchar
);

CREATE TABLE instance_1.flowapp_demo_order_consolidation (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id           uuid REFERENCES instance_1.flowapp_demo_order_head(id),
    consolidation_type  varchar NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_address_data (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id           uuid REFERENCES instance_1.flowapp_demo_order_head(id),
    address_category_id uuid REFERENCES instance_1.flowapp_demo_address_category(id),
    name                varchar,
    country_id          uuid REFERENCES instance_1.flowapp_demo_country_code(id)
);

-- ------------------------------------------------------------
-- Tasks / Buchungen
-- ------------------------------------------------------------
CREATE TABLE instance_1.flowapp_demo_task_booking_class (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_base   varchar NOT NULL,
    alias          varchar NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_task_head (
    id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_state               varchar NOT NULL DEFAULT '10',
    task_booking_class_id    uuid REFERENCES instance_1.flowapp_demo_task_booking_class(id),
    updated_date             timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE instance_1.flowapp_demo_task_position (
    id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_head_id              uuid REFERENCES instance_1.flowapp_demo_task_head(id),
    order_position_id         uuid REFERENCES instance_1.flowapp_demo_order_position(id),
    storage_date              timestamp,
    planned_processing_date   timestamp
);

CREATE TABLE instance_1.flowapp_demo_task_position_reference (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_position_id    uuid REFERENCES instance_1.flowapp_demo_task_position(id),
    reference_key       varchar,
    reference_value     varchar,
    source_slug_name    varchar
);

-- ------------------------------------------------------------
-- Handling Units, Bestand, Verpackung, Seriennummern
-- ------------------------------------------------------------
CREATE TABLE instance_1.flowapp_demo_handling_unit (
    id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    handling_unit_id         integer NOT NULL,
    handling_unit_number     varchar NOT NULL,
    storage_location_id      varchar,
    handling_unit_class_id   uuid REFERENCES instance_1.flowapp_demo_handling_unit_class(id)
);

CREATE TABLE instance_1.flowapp_demo_handling_unit_position (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    handling_unit_id   uuid REFERENCES instance_1.flowapp_demo_handling_unit(id),
    item_master_id     uuid REFERENCES instance_1.flowapp_demo_item_master(id)
);

CREATE TABLE instance_1.flowapp_demo_handling_unit_position_reference (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    handling_unit_position_id   uuid REFERENCES instance_1.flowapp_demo_handling_unit_position(id),
    reference_key               varchar,
    source_slug_name            varchar,
    reference_link              varchar,
    related_id                  uuid
);

CREATE TABLE instance_1.flowapp_demo_stock_quant (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    handling_unit_position_id   uuid REFERENCES instance_1.flowapp_demo_handling_unit_position(id),
    batch_a                     varchar,
    batch_b                     varchar,
    quantity                    numeric,
    quantity_unit_id            uuid REFERENCES instance_1.flowapp_demo_quantity_unit(id),
    customs_status_id           uuid REFERENCES instance_1.flowapp_demo_customs_status_profile(id),
    country_of_origin_id        uuid REFERENCES instance_1.flowapp_demo_country_code(id),
    updated_date                timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE instance_1.flowapp_demo_hu_position_serial_number (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id      uuid REFERENCES instance_1.flowapp_demo_handling_unit_position(id),
    serial_number  varchar NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_handling_unit_identification (
    id                              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    handling_unit_id                uuid REFERENCES instance_1.flowapp_demo_handling_unit(id),
    identification_type_id          uuid REFERENCES instance_1.flowapp_demo_handling_unit_identification_type(id),
    handling_unit_identification    varchar NOT NULL
);

CREATE TABLE instance_1.flowapp_demo_packaging_structure (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id  uuid REFERENCES instance_1.flowapp_demo_item_master(id)
);

CREATE TABLE instance_1.flowapp_demo_packaging_structure_pos (
    id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    packaging_structure_id  uuid REFERENCES instance_1.flowapp_demo_packaging_structure(id),
    packaging_level         integer NOT NULL,
    net_weight_g            integer,
    gross_weight_g          integer,
    length_mm               integer,
    width_mm                integer,
    height_mm               integer,
    bundling_unit_id        uuid REFERENCES instance_1.flowapp_demo_bundling_unit(id)
);

-- ------------------------------------------------------------
-- Print-Subscriptions
-- ------------------------------------------------------------
CREATE TABLE subscription.processevents_printer (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type   varchar NOT NULL,
    payload      jsonb,
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- Beispieldaten
-- ============================================================

INSERT INTO instance_1.flowapp_demo_quantity_unit (id, alias) VALUES
 ('13131313-0000-0000-0000-000000000001','piece'),
 ('13131313-0000-0000-0000-000000000002','kg');

INSERT INTO instance_1.flowapp_demo_order_class (id, alias, name) VALUES
 ('12121212-0000-0000-0000-000000000001','warenausgang','{"de":"Warenausgang","en":"Goods issue"}'),
 ('12121212-0000-0000-0000-000000000002','wareneingang','{"de":"Wareneingang","en":"Goods receipt"}'),
 ('12121212-0000-0000-0000-000000000003','sendung',     '{"de":"Sendung","en":"Shipment"}');

INSERT INTO instance_1.flowapp_demo_country_code (id, iso_code, name) VALUES
 ('17171717-0000-0000-0000-000000000001','DE','{"de":"Deutschland","en":"Germany"}'),
 ('17171717-0000-0000-0000-000000000002','CN','{"de":"China","en":"China"}'),
 ('17171717-0000-0000-0000-000000000003','AT','{"de":"Oesterreich","en":"Austria"}');

INSERT INTO instance_1.flowapp_demo_incoterm (id, alias, name) VALUES
 ('1a1a1a1a-0000-0000-0000-000000000001','DAP','Delivered At Place'),
 ('1a1a1a1a-0000-0000-0000-000000000002','EXW','Ex Works');

INSERT INTO instance_1.flowapp_demo_customs_status_profile (id, alias, name) VALUES
 ('18181818-0000-0000-0000-000000000001','verzollt',  '{"de":"verzollt","en":"cleared"}'),
 ('18181818-0000-0000-0000-000000000002','unverzollt','{"de":"unverzollt","en":"bonded"}');

INSERT INTO instance_1.flowapp_demo_customs_procedure_profile (id, alias, name) VALUES
 ('19191919-0000-0000-0000-000000000001','aes','{"de":"AES Ausfuhr","en":"AES export"}');

INSERT INTO instance_1.flowapp_demo_address_category (id, alias, name) VALUES
 ('16161616-0000-0000-0000-000000000001','lieferadresse',    '{"de":"Consignee (Lieferadresse)","en":"Consignee"}'),
 ('16161616-0000-0000-0000-000000000002','absenderadresse',  '{"de":"Consignor (Absender)","en":"Consignor"}'),
 ('16161616-0000-0000-0000-000000000003','rechnungsadresse', '{"de":"Billing (Rechnung)","en":"Billing"}');

INSERT INTO instance_1.flowapp_demo_bundling_unit (id, alias) VALUES
 ('1b1b1b1b-0000-0000-0000-000000000001','palette-typ-a'),
 ('1b1b1b1b-0000-0000-0000-000000000002','palette-typ-b');

INSERT INTO instance_1.flowapp_demo_handling_unit_class (id, alias) VALUES
 ('14141414-0000-0000-0000-000000000001','palette');

INSERT INTO instance_1.flowapp_demo_handling_unit_identification_type (id, alias) VALUES
 ('15151515-0000-0000-0000-000000000001','externe-tracking-nummer'),
 ('15151515-0000-0000-0000-000000000002','interne-hu');

INSERT INTO instance_1.flowapp_demo_client (id, code, alias, name, accounting_area_item_master_id) VALUES
 ('11111111-0000-0000-0000-000000000001','NORD',    'NORD',    '{"de":"Mandant Nord","en":"Client North"}',     'aaaaaaaa-0000-0000-0000-000000000001'),
 ('11111111-0000-0000-0000-000000000002','SUED',    'SUED',    '{"de":"Mandant Sued","en":"Client South"}',     'aaaaaaaa-0000-0000-0000-000000000002'),
 ('11111111-0000-0000-0000-000000000003','WEST',    'WEST',    '{"de":"Mandant West","en":"Client West"}',      'aaaaaaaa-0000-0000-0000-000000000003'),
 ('11111111-0000-0000-0000-000000000004','OST',     'OST',     '{"de":"Mandant Ost","en":"Client East"}',       'aaaaaaaa-0000-0000-0000-000000000004'),
 ('11111111-0000-0000-0000-000000000005','ZENTRAL', 'ZENTRAL', '{"de":"Mandant Zentral","en":"Client Central"}', 'aaaaaaaa-0000-0000-0000-000000000005'),
 ('11111111-0000-0000-0000-000000000006','DEMO',    'DEMO',    '{"de":"Uebungmandant","en":"Practice client"}', 'aaaaaaaa-0000-0000-0000-000000000006');

INSERT INTO instance_1.flowapp_demo_item_category (id, designation) VALUES
 ('22222222-0000-0000-0000-000000000001', '{"de":"Elektronik","en":"Electronics"}'),
 ('22222222-0000-0000-0000-000000000002', '{"de":"Getraenke","en":"Beverages"}');

INSERT INTO instance_1.flowapp_demo_item_master
    (id, parent_id, designation_a, item_group, cat_item_group_id, quantity_unit_id, customs_tariff_number_taric)
VALUES
 ('33333333-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001','{"de":"Bauteil A1","en":"Part A1"}', NULL, '22222222-0000-0000-0000-000000000001', '13131313-0000-0000-0000-000000000001', '85443000'),
 ('33333333-0000-0000-0000-000000000002','aaaaaaaa-0000-0000-0000-000000000002','{"de":"Platine B2","en":"Board B2"}', 'Elektronik', NULL, '13131313-0000-0000-0000-000000000001', '85371091'),
 ('33333333-0000-0000-0000-000000000003','aaaaaaaa-0000-0000-0000-000000000004','{"de":"Getraenk 250ml","en":"Drink 250ml"}', NULL, '22222222-0000-0000-0000-000000000002', '13131313-0000-0000-0000-000000000001', '22021000');

INSERT INTO instance_1.flowapp_demo_task_booking_class (id, booking_base, alias) VALUES
 ('44444444-0000-0000-0000-000000000001','1100','goods-receipt-single-hu-movement'),
 ('44444444-0000-0000-0000-000000000002','3100','outgoing-goods-single-hu-movement');

INSERT INTO instance_1.flowapp_demo_order_head (
    id, order_id, order_number, client_id, order_class_id, task_status, putaway_status, loading_status,
    packaging_status, shipment_number, planned_processing_date, confirmed_end_date_time, created_date,
    customs_procedures_id, incoterms_id
) VALUES
 ('55555555-0000-0000-0000-000000000001', 100501, '100501_A',
  '11111111-0000-0000-0000-000000000001', '12121212-0000-0000-0000-000000000002',
  '80', '80', '--', '00', NULL,
  TIMESTAMP '2026-09-01 06:00:00', TIMESTAMPTZ '2026-09-01 08:10:00+02', TIMESTAMPTZ '2026-08-31 09:00:00+02',
  NULL, NULL),
 ('55555555-0000-0000-0000-000000000002', 100502, '100502_A',
  '11111111-0000-0000-0000-000000000004', '12121212-0000-0000-0000-000000000001',
  '10', '00', '10', '10', NULL,
  TIMESTAMP '2026-09-08 06:00:00', NULL, TIMESTAMPTZ '2026-09-07 11:00:00+02',
  '19191919-0000-0000-0000-000000000001', '1a1a1a1a-0000-0000-0000-000000000001'),
 ('55555555-0000-0000-0000-000000000003', 100503, '100503_A',
  '11111111-0000-0000-0000-000000000002', '12121212-0000-0000-0000-000000000001',
  'X0', '00', '00', '00', NULL,
  TIMESTAMP '2026-09-05 06:00:00', NULL, TIMESTAMPTZ '2026-09-04 10:00:00+02',
  NULL, NULL),
 ('55555555-0000-0000-0000-000000000004', 100504, '100504_A',
  '11111111-0000-0000-0000-000000000003', '12121212-0000-0000-0000-000000000001',
  '80', '00', '80', '80', 'SHP-01',
  TIMESTAMP '2026-09-06 06:00:00', TIMESTAMPTZ '2026-09-06 16:40:00+02', TIMESTAMPTZ '2026-09-05 08:00:00+02',
  '19191919-0000-0000-0000-000000000001', '1a1a1a1a-0000-0000-0000-000000000001'),
 ('55555555-0000-0000-0000-000000000005', 100505, '100505_A',
  '11111111-0000-0000-0000-000000000003', '12121212-0000-0000-0000-000000000001',
  '40', '00', '40', '40', 'SHP-01',
  TIMESTAMP '2026-09-06 06:00:00', NULL, TIMESTAMPTZ '2026-09-05 08:30:00+02',
  '19191919-0000-0000-0000-000000000001', '1a1a1a1a-0000-0000-0000-000000000001'),
 ('55555555-0000-0000-0000-000000000006', 100506, 'SHP-01',
  '11111111-0000-0000-0000-000000000003', '12121212-0000-0000-0000-000000000003',
  '80', '00', '80', '80', 'SHP-01',
  TIMESTAMP '2026-09-06 06:00:00', TIMESTAMPTZ '2026-09-06 17:10:00+02', TIMESTAMPTZ '2026-09-05 07:00:00+02',
  NULL, '1a1a1a1a-0000-0000-0000-000000000001'),
 ('55555555-0000-0000-0000-000000000007', 100507, '100507_A',
  '11111111-0000-0000-0000-000000000005', '12121212-0000-0000-0000-000000000001',
  '10', '00', '--', '--', NULL,
  TIMESTAMP '2026-09-09 06:00:00', NULL, TIMESTAMPTZ '2026-09-09 15:30:00+02',
  NULL, '1a1a1a1a-0000-0000-0000-000000000002');

INSERT INTO instance_1.flowapp_demo_order_position (id, order_head_id, item_master_id, quantity) VALUES
 ('66666666-0000-0000-0000-000000000001','55555555-0000-0000-0000-000000000001','33333333-0000-0000-0000-000000000001', 20),
 ('66666666-0000-0000-0000-000000000002','55555555-0000-0000-0000-000000000002','33333333-0000-0000-0000-000000000003', 500),
 ('66666666-0000-0000-0000-000000000003','55555555-0000-0000-0000-000000000004','33333333-0000-0000-0000-000000000002', 12);

INSERT INTO instance_1.flowapp_demo_order_position_reference (id, order_position_id, reference_key, reference_value, source_slug_name) VALUES
 ('77777777-0000-0000-0000-000000000001','66666666-0000-0000-0000-000000000001','#X.order-id-pos','100501-1','order-position');

INSERT INTO instance_1.flowapp_demo_order_consolidation (id, parent_id, consolidation_type) VALUES
 ('88888888-0000-0000-0000-000000000001','55555555-0000-0000-0000-000000000001','1'),
 ('88888888-0000-0000-0000-000000000002','55555555-0000-0000-0000-000000000001','5'),
 ('88888888-0000-0000-0000-000000000003','55555555-0000-0000-0000-000000000002','3');

INSERT INTO instance_1.flowapp_demo_address_data (id, parent_id, address_category_id, name, country_id) VALUES
 ('a1a1a1a1-0000-0000-0000-000000000001','55555555-0000-0000-0000-000000000004','16161616-0000-0000-0000-000000000001','Werk West Brno','17171717-0000-0000-0000-000000000003'),
 ('a1a1a1a1-0000-0000-0000-000000000002','55555555-0000-0000-0000-000000000004','16161616-0000-0000-0000-000000000002','Lager West DE','17171717-0000-0000-0000-000000000001'),
 ('a1a1a1a1-0000-0000-0000-000000000003','55555555-0000-0000-0000-000000000004','16161616-0000-0000-0000-000000000003','Rechnung West','17171717-0000-0000-0000-000000000001');

INSERT INTO instance_1.flowapp_demo_task_head (id, task_state, task_booking_class_id, updated_date) VALUES
 ('99999999-0000-0000-0000-000000000001','90','44444444-0000-0000-0000-000000000001', now() - interval '2 days'),
 ('99999999-0000-0000-0000-000000000002','10','44444444-0000-0000-0000-000000000002', now() - interval '1 hour'),
 ('99999999-0000-0000-0000-000000000003','90','44444444-0000-0000-0000-000000000002', now() - interval '3 days'),
 ('99999999-0000-0000-0000-000000000004','90','44444444-0000-0000-0000-000000000001', now() - interval '4 hours');

INSERT INTO instance_1.flowapp_demo_task_position (id, task_head_id, order_position_id, storage_date, planned_processing_date) VALUES
 ('aaaaaaab-0000-0000-0000-000000000001','99999999-0000-0000-0000-000000000001','66666666-0000-0000-0000-000000000001', now() - interval '2 days', now() - interval '3 days'),
 ('aaaaaaab-0000-0000-0000-000000000002','99999999-0000-0000-0000-000000000002','66666666-0000-0000-0000-000000000002', NULL, now() + interval '1 day'),
 ('aaaaaaab-0000-0000-0000-000000000003','99999999-0000-0000-0000-000000000003','66666666-0000-0000-0000-000000000003', now() - interval '3 days', now() - interval '4 days'),
 ('aaaaaaab-0000-0000-0000-000000000004','99999999-0000-0000-0000-000000000004','66666666-0000-0000-0000-000000000001', NULL, now() - interval '5 hours');

INSERT INTO instance_1.flowapp_demo_task_position_reference (id, task_position_id, reference_key, reference_value, source_slug_name) VALUES
 ('bbbbbbbb-0000-0000-0000-000000000001','aaaaaaab-0000-0000-0000-000000000001','#X.order-id','100501','order-head'),
 ('bbbbbbbb-0000-0000-0000-000000000002','aaaaaaab-0000-0000-0000-000000000002','#X.order-id','100502','order-head');

INSERT INTO instance_1.flowapp_demo_handling_unit (id, handling_unit_id, handling_unit_number, storage_location_id, handling_unit_class_id) VALUES
 ('cccccccc-0000-0000-0000-000000000001', 500101, 'HU-500101', 'A-01-02-3', '14141414-0000-0000-0000-000000000001'),
 ('cccccccc-0000-0000-0000-000000000002', 500102, 'HU-500102', 'B-04-01-1', '14141414-0000-0000-0000-000000000001');

INSERT INTO instance_1.flowapp_demo_handling_unit_position (id, handling_unit_id, item_master_id) VALUES
 ('dddddddd-0000-0000-0000-000000000001','cccccccc-0000-0000-0000-000000000001','33333333-0000-0000-0000-000000000001'),
 ('dddddddd-0000-0000-0000-000000000002','cccccccc-0000-0000-0000-000000000002','33333333-0000-0000-0000-000000000003');

INSERT INTO instance_1.flowapp_demo_handling_unit_position_reference (id, handling_unit_position_id, reference_key, source_slug_name, reference_link, related_id) VALUES
 ('eeeeeeee-0000-0000-0000-000000000001','dddddddd-0000-0000-0000-000000000001','#X.order-id-pos','order-position', NULL, NULL),
 ('eeeeeeee-0000-0000-0000-000000000002','dddddddd-0000-0000-0000-000000000002', NULL, NULL, 'product-outgoing-order', '66666666-0000-0000-0000-000000000002');

-- HU 1: neueste Qualifikation hat falsche Einheit (kg statt piece) — Fall K.4
INSERT INTO instance_1.flowapp_demo_stock_quant
    (id, handling_unit_position_id, batch_a, batch_b, quantity, quantity_unit_id, customs_status_id, country_of_origin_id, updated_date)
VALUES
 ('ffffffff-0000-0000-0000-000000000001','dddddddd-0000-0000-0000-000000000001','B2024-01','L1', 20, '13131313-0000-0000-0000-000000000001', '18181818-0000-0000-0000-000000000002', '17171717-0000-0000-0000-000000000002', now() - interval '5 days'),
 ('ffffffff-0000-0000-0000-000000000002','dddddddd-0000-0000-0000-000000000001','B2024-02','L2', 20, '13131313-0000-0000-0000-000000000002', '18181818-0000-0000-0000-000000000002', '17171717-0000-0000-0000-000000000002', now() - interval '1 days'),
 ('ffffffff-0000-0000-0000-000000000003','dddddddd-0000-0000-0000-000000000002','B2024-05','L1', 500,'13131313-0000-0000-0000-000000000001', '18181818-0000-0000-0000-000000000001', '17171717-0000-0000-0000-000000000003', now() - interval '2 days');

INSERT INTO instance_1.flowapp_demo_hu_position_serial_number (id, parent_id, serial_number) VALUES
 ('2c2c2c2c-0000-0000-0000-000000000001','dddddddd-0000-0000-0000-000000000001','SN-A1-1001'),
 ('2c2c2c2c-0000-0000-0000-000000000002','dddddddd-0000-0000-0000-000000000001','SN-A1-1002'),
 ('2c2c2c2c-0000-0000-0000-000000000003','dddddddd-0000-0000-0000-000000000001','SN-A1-1003');

INSERT INTO instance_1.flowapp_demo_handling_unit_identification
    (id, handling_unit_id, identification_type_id, handling_unit_identification)
VALUES
 ('2d2d2d2d-0000-0000-0000-000000000001','cccccccc-0000-0000-0000-000000000002','15151515-0000-0000-0000-000000000001','TNR-9001');

INSERT INTO instance_1.flowapp_demo_packaging_structure (id, parent_id) VALUES
 ('1c1c1c1c-0000-0000-0000-000000000001','33333333-0000-0000-0000-000000000001');

INSERT INTO instance_1.flowapp_demo_packaging_structure_pos
    (id, packaging_structure_id, packaging_level, net_weight_g, gross_weight_g, length_mm, width_mm, height_mm, bundling_unit_id)
VALUES
 ('1d1d1d1d-0000-0000-0000-000000000001','1c1c1c1c-0000-0000-0000-000000000001', 0, 420, 450, 300, 200, 80, NULL),
 ('1d1d1d1d-0000-0000-0000-000000000002','1c1c1c1c-0000-0000-0000-000000000001', 3, 8400, 9200, 1200, 800, 1440, '1b1b1b1b-0000-0000-0000-000000000001');

INSERT INTO subscription.processevents_printer (event_type, payload) VALUES
 ('label-print-requested', '{"printer":"HALLE1-PR3","hu":500101}'),
 ('label-print-confirmed', '{"printer":"HALLE1-PR3","hu":500101}');

-- ============================================================
-- Read-only Lern-User
-- ============================================================
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lernuser') THEN
      CREATE ROLE lernuser LOGIN PASSWORD 'lernuser';
   END IF;
END
$$;

GRANT USAGE ON SCHEMA instance_1, subscription TO lernuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA instance_1 TO lernuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA subscription TO lernuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA instance_1 GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lernuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA subscription GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lernuser;

ALTER ROLE lernuser SET statement_timeout = '5s';
