
SQL IMOBLY:

-- public.contracts definition

-- Drop table

-- DROP TABLE public.contracts;

CREATE TABLE public.contracts (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	title varchar(255) NOT NULL,
	property_id int4 NOT NULL,
	tenant_id int4 NOT NULL,
	start_date date NOT NULL,
	end_date date NOT NULL,
	rent numeric(10, 2) NOT NULL,
	deposit numeric(10, 2) NOT NULL,
	interest_rate numeric(5, 2) NOT NULL,
	fine_rate numeric(5, 2) NOT NULL,
	status varchar(20) NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT contracts_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_contracts_id ON public.contracts USING btree (id);
CREATE INDEX ix_contracts_user_id ON public.contracts USING btree (user_id);


-- public.contracts foreign keys

ALTER TABLE public.contracts ADD CONSTRAINT fk_contract_property_id FOREIGN KEY (property_id) REFERENCES public.properties(id);
ALTER TABLE public.contracts ADD CONSTRAINT fk_contract_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);



-- public.expenses definition

-- Drop table

-- DROP TABLE public.expenses;

CREATE TABLE public.expenses (
	id varchar(36) NOT NULL,
	user_id int4 NOT NULL,
	"type" varchar(20) NOT NULL,
	category varchar(100) NOT NULL,
	description text NOT NULL,
	amount numeric(10, 2) NOT NULL,
	"date" date NOT NULL,
	property_id int4 NOT NULL,
	status varchar(20) NOT NULL,
	priority varchar(20) NULL,
	vendor varchar(255) NULL,
	"number" varchar(20) NULL,
	receipt text NULL,
	documents jsonb NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT expenses_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_expenses_user_id ON public.expenses USING btree (user_id);


-- public.expenses foreign keys

ALTER TABLE public.expenses ADD CONSTRAINT expenses_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id);





-- public.notifications definition

-- Drop table

-- DROP TABLE public.notifications;

CREATE TABLE public.notifications (
	id varchar(36) NOT NULL,
	user_id int4 NOT NULL,
	"type" varchar(50) NOT NULL,
	title varchar(255) NOT NULL,
	message text NOT NULL,
	"date" timestamp NOT NULL,
	priority varchar(20) NOT NULL,
	read_status bool NULL,
	action_required bool NULL,
	related_id varchar(255) NULL,
	related_type varchar(50) NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT notifications_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_notifications_user_id ON public.notifications USING btree (user_id);





-- public.payments definition

-- Drop table

-- DROP TABLE public.payments;

CREATE TABLE public.payments (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	property_id int4 NOT NULL,
	tenant_id int4 NOT NULL,
	contract_id int4 NOT NULL,
	due_date date NOT NULL,
	payment_date date NULL,
	amount numeric(10, 2) NOT NULL,
	fine_amount numeric(10, 2) NULL,
	total_amount numeric(10, 2) NOT NULL,
	status varchar(20) NOT NULL,
	payment_method varchar(20) NULL,
	description text NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT payments_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_payments_id ON public.payments USING btree (id);
CREATE INDEX ix_payments_user_id ON public.payments USING btree (user_id);


-- public.payments foreign keys

ALTER TABLE public.payments ADD CONSTRAINT payments_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.contracts(id);
ALTER TABLE public.payments ADD CONSTRAINT payments_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id);
ALTER TABLE public.payments ADD CONSTRAINT payments_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);



-- public.properties definition

-- Drop table

-- DROP TABLE public.properties;

CREATE TABLE public.properties (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	"name" varchar(255) NOT NULL,
	address text NOT NULL,
	neighborhood varchar(100) NOT NULL,
	city varchar(100) NOT NULL,
	state varchar(50) NOT NULL,
	zip_code varchar(20) NOT NULL,
	"type" varchar(50) NOT NULL,
	area numeric(10, 2) NOT NULL,
	bedrooms int4 NOT NULL,
	bathrooms int4 NOT NULL,
	parking_spaces int4 NULL,
	rent numeric(10, 2) NOT NULL,
	status varchar(20) NULL,
	description text NULL,
	images json NULL,
	is_residential bool NULL,
	tenant_id int4 NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT properties_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_properties_id ON public.properties USING btree (id);
CREATE INDEX ix_properties_tenant_id ON public.properties USING btree (tenant_id);
CREATE INDEX ix_properties_user_id ON public.properties USING btree (user_id);


-- public.properties foreign keys

ALTER TABLE public.properties ADD CONSTRAINT fk_property_tenant_id FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE SET NULL;





-- public.tenants definition

-- Drop table

-- DROP TABLE public.tenants;

CREATE TABLE public.tenants (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	"name" varchar(255) NOT NULL,
	email varchar(255) NOT NULL,
	phone varchar(20) NOT NULL,
	cpf_cnpj varchar(20) NOT NULL,
	birth_date date NULL,
	profession varchar(100) NOT NULL,
	emergency_contact json NULL,
	documents json NULL,
	contract_id int4 NULL,
	status varchar(20) NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT tenants_cpf_cnpj_key UNIQUE (cpf_cnpj),
	CONSTRAINT tenants_email_key UNIQUE (email),
	CONSTRAINT tenants_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_tenants_id ON public.tenants USING btree (id);
CREATE INDEX ix_tenants_user_id ON public.tenants USING btree (user_id);


-- public.tenants foreign keys

ALTER TABLE public.tenants ADD CONSTRAINT fk_tenant_contract_id FOREIGN KEY (contract_id) REFERENCES public.contracts(id);




-- public.units definition

-- Drop table

-- DROP TABLE public.units;

CREATE TABLE public.units (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	property_id int4 NOT NULL,
	"number" varchar(50) NOT NULL,
	area numeric(10, 2) NOT NULL,
	bedrooms int4 NOT NULL,
	bathrooms int4 NOT NULL,
	rent numeric(10, 2) NOT NULL,
	status varchar(20) NOT NULL,
	tenant varchar(255) NULL,
	created_at timestamp NULL,
	updated_at timestamp NULL,
	CONSTRAINT units_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_units_id ON public.units USING btree (id);
CREATE INDEX ix_units_user_id ON public.units USING btree (user_id);


-- public.units foreign keys

ALTER TABLE public.units ADD CONSTRAINT units_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id);