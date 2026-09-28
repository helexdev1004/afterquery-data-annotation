-- visible dataset

DROP TABLE IF EXISTS line_items, payments, invoices, customers, regions;

CREATE TABLE regions (
  code        varchar(4)   NOT NULL,
  name        varchar(40)  NOT NULL,
  PRIMARY KEY (code)
);

CREATE TABLE customers (
  id            integer      NOT NULL,
  name          varchar(60)  NOT NULL,
  region_code   varchar(4)   NOT NULL,
  tier          varchar(10)  NOT NULL,
  signup_date   date         NOT NULL,
  active        boolean      NOT NULL,
  external_ref  varchar(20)  NULL,
  PRIMARY KEY (id)
);

CREATE TABLE invoices (
  id            integer      NOT NULL,
  customer_id   integer      NOT NULL,
  issued_on     date         NOT NULL,
  amount_cents  integer      NOT NULL,
  qty           integer      NOT NULL,
  discount_pct  integer      NOT NULL,
  currency      varchar(3)   NOT NULL,
  status        varchar(12)  NOT NULL,
  PRIMARY KEY (id)
);

CREATE TABLE payments (
  id            integer      NOT NULL,
  invoice_id    integer      NOT NULL,
  paid_at       timestamp    NOT NULL,
  amount_cents  integer      NOT NULL,
  method        varchar(12)  NOT NULL,
  note          varchar(60)  NULL,
  PRIMARY KEY (id)
);

CREATE TABLE line_items (
  id            integer      NOT NULL,
  invoice_id    integer      NOT NULL,
  sku           varchar(20)  NOT NULL,
  units         integer      NOT NULL,
  unit_cents    integer      NOT NULL,
  category      varchar(20)  NULL,
  PRIMARY KEY (id)
);

