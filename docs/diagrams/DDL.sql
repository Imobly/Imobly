-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.
--
-- CONTRACT STATUS: 'ativo', 'inativo', 'expirado'
-- TENANT STATUS: derived from contract at query time (no status column)

CREATE TABLE public.contracts (
  id integer NOT NULL DEFAULT nextval('contracts_id_seq'::regclass),
  user_id integer NOT NULL,
  title character varying NOT NULL,
  property_id integer NOT NULL,
  tenant_id integer NOT NULL,
  start_date date NOT NULL,
  end_date date NOT NULL,
  rent numeric,
  deposit numeric NOT NULL,
  interest_rate numeric NOT NULL,
  fine_rate numeric NOT NULL,
  status character varying,
  created_at timestamp without time zone,
  updated_at timestamp without time zone,
  titulo character varying,
  titulozin character varying,
  CONSTRAINT contracts_pkey PRIMARY KEY (id),
  CONSTRAINT fk_contract_property_id FOREIGN KEY (property_id) REFERENCES public.properties(id),
  CONSTRAINT fk_contract_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id),
  CONSTRAINT contracts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.expenses (
  id character varying NOT NULL,
  user_id integer NOT NULL,
  type character varying NOT NULL,
  category character varying NOT NULL,
  description text NOT NULL,
  amount numeric NOT NULL,
  date date NOT NULL,
  property_id integer NOT NULL,
  status character varying NOT NULL,
  priority character varying,
  vendor character varying,
  number character varying,
  receipt text,
  documents jsonb,
  created_at timestamp without time zone,
  updated_at timestamp without time zone,
  CONSTRAINT expenses_pkey PRIMARY KEY (id),
  CONSTRAINT expenses_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id),
  CONSTRAINT expenses_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
create table public.notifications (
  id character varying(36) not null,
  user_id integer not null,
  type character varying(50) not null,
  title character varying(255) not null,
  message text not null,
  is_read boolean null,
  created_at timestamp without time zone null,
  updated_at timestamp without time zone null,
  link text null,
  metadata jsonb null,
  constraint notifications_pkey primary key (id),
  constraint notifications_user_id_fkey foreign KEY (user_id) references users (id)
) TABLESPACE pg_default;

create index IF not exists ix_notifications_user_id on public.notifications using btree (user_id) TABLESPACE pg_default;
CREATE TABLE public.payments (
  id integer NOT NULL DEFAULT nextval('payments_id_seq'::regclass),
  user_id integer NOT NULL,
  property_id integer NOT NULL,
  tenant_id integer NOT NULL,
  contract_id integer NOT NULL,
  due_date date NOT NULL,
  payment_date date,
  amount numeric NOT NULL,
  fine_amount numeric,
  total_amount numeric NOT NULL,
  status character varying NOT NULL,
  payment_method character varying,
  description text,
  created_at timestamp without time zone,
  updated_at timestamp without time zone,
  CONSTRAINT payments_pkey PRIMARY KEY (id),
  CONSTRAINT payments_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.contracts(id),
  CONSTRAINT payments_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id),
  CONSTRAINT payments_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id),
  CONSTRAINT payments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.properties (
  id integer NOT NULL DEFAULT nextval('properties_id_seq'::regclass),
  user_id integer NOT NULL,
  name character varying NOT NULL,
  address text NOT NULL,
  neighborhood character varying NOT NULL,
  city character varying NOT NULL,
  state character varying NOT NULL,
  zip_code character varying NOT NULL,
  type character varying NOT NULL,
  area numeric NOT NULL,
  bedrooms integer NOT NULL,
  bathrooms integer NOT NULL,
  parking_spaces integer,
  rent numeric NOT NULL,
  status character varying,
  description text,
  images json,
  tenant_id integer,
  created_at timestamp without time zone,
  updated_at timestamp without time zone,
  CONSTRAINT properties_pkey PRIMARY KEY (id),
  CONSTRAINT fk_property_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id),
  CONSTRAINT properties_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.tenants (
  id integer NOT NULL DEFAULT nextval('tenants_id_seq'::regclass),
  user_id integer NOT NULL,
  name character varying NOT NULL,
  email character varying NOT NULL UNIQUE,
  phone character varying NOT NULL,
  cpf_cnpj character varying NOT NULL UNIQUE,
  birth_date date,
  profession character varying NOT NULL,
  emergency_contact json,
  documents json,
  contract_id integer,
  created_at timestamp without time zone,
  updated_at timestamp without time zone,
  CONSTRAINT tenants_pkey PRIMARY KEY (id),
  CONSTRAINT fk_tenant_contract_id FOREIGN KEY (contract_id) REFERENCES public.contracts(id),
  CONSTRAINT tenants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.users (
  id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
  email character varying NOT NULL,
  username character varying NOT NULL,
  full_name character varying,
  hashed_password character varying NOT NULL,
  is_active boolean NOT NULL,
  is_superuser boolean NOT NULL,
  created_at timestamp without time zone NOT NULL,
  updated_at timestamp without time zone NOT NULL,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);