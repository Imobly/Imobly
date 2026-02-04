# Modelagem e Diagramas

Esta seção contém todos os diagramas e modelagens do sistema Imobly.

## Diagrama de Classes UML

O diagrama de classes mostra a estrutura principal do sistema:

![Diagrama de Classes](../image.png)

## Modelagem do Banco de Dados

### Modelo Conceitual

```mermaid
erDiagram
    Property ||--o{ Unit : has
    Property ||--o{ Contract : contains
    Property ||--o{ Expense : incurs
    
    Tenant ||--o{ Contract : signs
    Tenant ||--o{ Payment : makes
    
    Contract ||--o{ Payment : generates
    
    Unit ||--o{ Contract : rented_by
    
    Property {
        int id PK
        string name
        string address
        string city
        string state
        string zip_code
        enum type
        float area
        int bedrooms
        int bathrooms
        decimal rent_value
        enum status
        datetime created_at
        datetime updated_at
    }
    
    Unit {
        int id PK
        int property_id FK
        string identifier
        float area
        int bedrooms
        int bathrooms
        decimal rent_value
        enum status
    }
    
    Tenant {
        int id PK
        string name
        string email
        string phone
        string cpf_cnpj
        date birth_date
        string profession
        decimal income
        text address
        json emergency_contact
        enum status
        datetime created_at
        datetime updated_at
    }
    
    Contract {
        int id PK
        int property_id FK
        int unit_id FK
        int tenant_id FK
        string title
        date start_date
        date end_date
        decimal rent_value
        decimal deposit
        float interest_rate
        float fine_rate
        enum status
        text terms
        string document_url
        datetime created_at
        datetime updated_at
    }
    
    Payment {
        int id PK
        int contract_id FK
        int tenant_id FK
        date due_date
        date payment_date
        decimal amount
        decimal fine_amount
        decimal total_amount
        enum status
        enum payment_method
        text description
        datetime created_at
        datetime updated_at
    }
    
    Expense {
        int id PK
        int property_id FK
        string category
        string type
        text description
        decimal amount
        date expense_date
        enum status
        enum priority
        string vendor
        string receipt_url
        text notes
        datetime created_at
        datetime updated_at
    }
```

## Diagrama de Arquitetura

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web App<br/>Next.js]
        B[Mobile PWA]
        C[Admin Dashboard]
    end
    
    subgraph "API Layer"
        D[API Gateway<br/>FastAPI]
        E[Authentication Service]
        F[Business Logic]
    end
    
    subgraph "Data Layer"
        G[MySQL Database]
        H[Redis Cache]
        I[File Storage<br/>S3/MinIO]
    end
    
    subgraph "External Services"
        J[Email Service]
        K[SMS Service]
        L[Payment Gateway]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    E --> G
    F --> G
    F --> H
    F --> I
    F --> J
    F --> K
    F --> L
    
    style A fill:#e1f5fe
    style B fill:#e1f5fe
    style C fill:#e1f5fe
    style D fill:#f3e5f5
    style E fill:#f3e5f5
    style F fill:#f3e5f5
    style G fill:#e8f5e8
    style H fill:#e8f5e8
    style I fill:#e8f5e8
```

## Modelo Físico do Banco de Dados (DDL)

O script DDL completo para criação do banco de dados PostgreSQL está disponível em [`DDL.sql`](DDL.sql).

### Estrutura das Tabelas

#### Users (Usuários)
- Sistema de autenticação e gerenciamento de usuários

#### Properties (Propriedades)
```sql
- id (PK)
- user_id (FK)
- name, address, neighborhood, city, state, zip_code
- type, area, bedrooms, bathrooms, parking_spaces
- rent, status, description, images
- is_residential, tenant_id (FK)
```

#### Units (Unidades)
```sql
- id (PK)
- user_id (FK), property_id (FK)
- number, area, bedrooms, bathrooms
- rent, status, tenant
```

#### Tenants (Inquilinos)
```sql
- id (PK)
- user_id (FK)
- name, email, phone, cpf_cnpj
- birth_date, profession
- emergency_contact (JSON), documents (JSON)
- contract_id (FK), status
```

#### Contracts (Contratos)
```sql
- id (PK)
- user_id (FK), property_id (FK), tenant_id (FK)
- title, start_date, end_date
- rent, deposit, interest_rate, fine_rate
- status
```

#### Payments (Pagamentos)
```sql
- id (PK)
- user_id (FK), property_id (FK), tenant_id (FK), contract_id (FK)
- due_date, payment_date
- amount, fine_amount, total_amount
- status, payment_method, description
```

#### Expenses (Despesas)
```sql
- id (UUID)
- user_id (FK), property_id (FK)
- type, category, description, amount, date
- status, priority, vendor, number
- receipt, documents (JSONB)
```

#### Notifications (Notificações)
```sql
- id (UUID)
- user_id (FK)
- type, title, message, date, priority
- read_status, action_required
- related_id, related_type
```

### Relacionamentos

- **Properties** 1:N **Units** (uma propriedade pode ter várias unidades)
- **Properties** N:1 **Tenants** (propriedade pode ter inquilino atual)
- **Tenants** 1:N **Contracts** (inquilino pode ter múltiplos contratos)
- **Contracts** 1:N **Payments** (contrato gera múltiplos pagamentos)
- **Properties** 1:N **Expenses** (propriedade tem múltiplas despesas)

## Protótipos da Interface

### Documentos do Protótipo

Os protótipos completos do sistema Imobly estão disponíveis em PDF:

- **[📄 Protótipo Completo (PDF)](../prototypes/Protorype.pdf)** - Protótipo detalhado das telas do sistema
- **[📊 Diagrama UML (PDF)](../prototypes/diagramaUML.pdf)** - Diagrama de classes e estrutura

!!! tip "Visualização de PDFs"
    Para melhor visualização, baixe os PDFs e abra em um leitor de PDF. O navegador pode ter limitações de renderização.

## Próximos Diagramas

Esta seção será expandida com:

- **Diagrama de Sequência** - Fluxos de autenticação e operações
- **Diagrama de Casos de Uso** - Funcionalidades do sistema
- **Arquitetura de Deploy** - Infraestrutura de produção

## Arquivos Fonte

- **PlantUML:** `diagramaDeClasses.wsd` - Definição do diagrama de classes
- **DDL:** `DDL.sql` - Script de criação do banco de dados PostgreSQL