# SubNexus — AI-Powered Subscription Management & Revenue Intelligence

<p align="center">
  <strong>One workspace. Complete subscription lifecycle. Smarter revenue decisions.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react" alt="React"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Machine_Learning-Scikit--learn-orange?logo=scikitlearn" alt="Scikit-learn"/>
</p>

---

## Overview

**SubNexus** is an AI-powered subscription management and revenue intelligence platform designed to simplify recurring billing, manage customer subscriptions, streamline payment operations, and provide actionable business insights.

It brings subscription lifecycle management, customer management, invoicing, payment tracking, bank reconciliation, governance workflows, analytics, and machine-learning-based churn prediction into a unified workspace.

### The problem we solve

Subscription-based businesses often face challenges such as:

- Fragmented subscription and customer information.
- Manual invoice and payment tracking.
- Difficulty reconciling bank transactions with invoices.
- Limited visibility into recurring revenue and outstanding payments.
- Delayed identification of customers likely to churn.
- Lack of structured approval workflows and audit trails.

### Our solution

SubNexus provides a centralized platform with:

- End-to-end subscription lifecycle management.
- Unified customer, product, and plan management.
- Billing, invoices, payments, and refunds.
- Bank statement reconciliation.
- Revenue and subscription analytics.
- ML-powered customer churn prediction.
- Role-based access, approvals, notifications, and audit logs.

---

## Key Features

### 1. Authentication and User Management

- User registration and login.
- Password hashing and secure password verification.
- JWT-based authentication.
- Email verification workflow.
- Role-based access control.
- Separate customer, staff, and administrator experiences.
- Protected application routes and API endpoints.

### 2. Customer Management

- Create and manage customer records.
- View customer profiles and subscription information.
- Track customer status and associated plans.
- Monitor customer balances and outstanding amounts.
- Access customer-related billing and payment records.

### 3. Subscription Lifecycle Management

- Create subscriptions.
- Activate subscriptions.
- Pause and resume subscriptions.
- Renew subscriptions.
- Cancel subscriptions immediately or at the end of the billing period.
- Track subscription status and billing information.
- Maintain subscription event history.

**Illustrative lifecycle:** `Draft → Quotation → Confirmed → Active → Paused / Cancelled / Closed`

### 4. Product and Plan Catalog

- Product management.
- Subscription plan management.
- Plan pricing and billing information.
- Tax-rule visibility in the frontend catalog.
- Discount management.
- Discount validation.
- Discount activation and deactivation.

### 5. Quotation Management

- Create, view, and manage quotations.
- Send quotations.
- Accept or reject quotations.
- Cancel quotations.
- Associate quotations with customers.

### 6. Billing and Invoice Management

- Create and issue invoices.
- View invoice details and status.
- Track outstanding and overdue invoices.
- Cancel invoices.
- Connect billing records with customer and payment information.

### 7. Payment Management

- Create and track payment records.
- View payment history.
- Verify payments.
- Record failed payment attempts.
- Track payment attempts.
- Manage and view refunds.

### 8. Bank Reconciliation

- Import bank statements through CSV upload.
- Validate transaction data.
- Detect duplicate or invalid records.
- View unmatched transactions.
- Propose transaction-to-payment matches.
- Review and confirm suggested matches.
- Track reconciliation status.

The reconciliation API supports CSV imports with transaction date, amount, and currency fields, along with optional reference and customer information.

### 9. Revenue and Business Analytics

- Revenue analytics.
- Monthly Recurring Revenue (MRR).
- Annual Recurring Revenue (ARR).
- Churn analytics.
- Subscription analytics.
- Outstanding payment analytics.
- Top customers.
- Top-performing plans.

### 10. AI-Powered Customer Churn Prediction

SubNexus includes a machine-learning module to estimate the likelihood of a customer discontinuing their subscription.

**Prediction inputs include:**

- Customer tenure and monthly charges.
- Payment failures in the last 90 days.
- Days since the last payment.
- Support tickets in the last 90 days.
- Usage sessions in the last 30 days.
- Subscription plan type and discount usage.
- Renewal count and auto-renewal status.
- Late payment count.

**Model pipeline:**

1. Dataset preparation and preprocessing.
2. Numerical feature scaling.
3. Categorical feature encoding.
4. Random Forest model training.
5. Churn probability prediction.
6. Risk-level classification.
7. Retention recommendation generation.

**Model output:** churn probability, churn percentage, risk level (Low / Medium / High), recommended retention action, and model version.

**Current prototype model information**

| Metric | Result |
|---|---:|
| Algorithm | Random Forest |
| Dataset size | 5,000 records |
| Accuracy | 77.30% |
| Precision | 33.17% |
| Recall | 43.95% |
| F1-score | 37.81% |
| ROC-AUC | 72.66% |

The current model was trained using a synthetic dataset for prototyping. These metrics are experimental and should not be interpreted as production-validated performance.

**API endpoint:** `POST /api/v1/churn/predict` — restricted to authorized staff and administrators.

### 11. Governance, Approvals and Audit Trail

- Create, list, and view approval requests.
- Approve or reject requests.
- Assign approval permissions to users.
- Record approval decisions.
- Maintain audit logs.
- Filter audit logs by user, action, entity, and date.
- Generate approval-related notifications.
- Mark individual or all notifications as read.

Approval workflows cover exceptional discounts, invoice cancellation, subscription closure, refunds, and quotation review.

### 12. AI Assistant Workspace

The frontend includes an Assistant workspace designed around subscription and revenue-related questions, with evidence-oriented responses and suggested actions.

Example prompts include:

- Which subscriptions expire this month?
- Why are payments unmatched?
- Why did revenue change?

The assistant interface is a prototype workspace; its displayed example responses should not be interpreted as a fully integrated autonomous AI agent.

---

## Application Architecture

SubNexus follows a modular full-stack architecture. The React frontend communicates with FastAPI REST endpoints, while the backend handles authentication, business logic, database operations, and ML inference.

### High-Level Architecture

```mermaid
flowchart TB
    U["Users: Admin / Staff / Customer"]

    subgraph FE["Frontend Layer"]
        UI["React + TypeScript"]
        ROUTES["React Router"]
        MODULES["Dashboard, Customers, Subscriptions, Billing, Insights"]
        UI --> ROUTES --> MODULES
    end

    subgraph API["Backend Layer"]
        APIAPP["FastAPI Application"]
        AUTH["Authentication & RBAC"]
        SERVICES["Business Logic Services"]
        ROUTERS["REST API Routers"]
        GOV["Governance & Audit"]
        APIAPP --> AUTH
        APIAPP --> ROUTERS
        ROUTERS --> SERVICES
        SERVICES --> GOV
    end

    subgraph DATA["Data Layer"]
        ORM["SQLAlchemy ORM"]
        DB[("PostgreSQL")]
        ORM --> DB
    end

    subgraph ML["Machine Learning Layer"]
        PRE["Preprocessing Pipeline"]
        RF["Random Forest Model"]
        PRED["Churn Prediction & Risk Assessment"]
        PRE --> RF --> PRED
    end

    U --> FE
    FE <-->|"HTTP / JSON"| APIAPP
    SERVICES <--> ORM
    SERVICES --> ML
```

### Request Flow

1. A user interacts with the React frontend.
2. The frontend sends HTTP requests to the FastAPI backend.
3. Authentication and role-based permissions are checked.
4. The relevant router invokes its business service.
5. SQLAlchemy handles database operations with PostgreSQL.
6. For churn prediction, the backend loads the trained ML pipeline and performs inference.
7. The backend returns structured JSON responses to the frontend.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript |
| Frontend tooling | Vite |
| Routing | React Router |
| Icons | Lucide React |
| Backend | Python, FastAPI |
| API validation | Pydantic |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Database migrations | Alembic |
| Authentication | JWT |
| Password security | pwdlib / Argon2 |
| Machine Learning | Scikit-learn |
| Data processing | NumPy, Pandas |
| Data visualization | Matplotlib, Seaborn |
| API documentation | Swagger UI / OpenAPI |
| Version control | Git and GitHub |

---

## Project Structure

```text
SubNexus-hackathon-odoo/
│
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── dependencies.py
│   │   ├── database/
│   │   │   ├── db.py
│   │   │   ├── base.py
│   │   │   └── init_db.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── customer.py
│   │   │   ├── subscription.py
│   │   │   ├── plan.py
│   │   │   ├── product.py
│   │   │   ├── quotation.py
│   │   │   ├── invoice.py
│   │   │   ├── payment.py
│   │   │   ├── discount.py
│   │   │   ├── reconciliation.py
│   │   │   ├── approval.py
│   │   │   └── log.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── admin.py
│   │   │   ├── customers.py
│   │   │   ├── products.py
│   │   │   ├── plans.py
│   │   │   ├── subscriptions.py
│   │   │   ├── quotations.py
│   │   │   ├── invoices.py
│   │   │   ├── payments.py
│   │   │   ├── discounts.py
│   │   │   ├── reconciliation.py
│   │   │   ├── analytics.py
│   │   │   ├── governance.py
│   │   │   └── churn.py
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── ml/
│   │   ├── data/
│   │   │   └── churn_dataset.csv
│   │   ├── models/
│   │   │   ├── churn_model.pkl
│   │   │   ├── model_metrics.csv
│   │   │   └── feature_importance.csv
│   │   └── src/
│   │       ├── generate_data.py
│   │       ├── analyze_data.py
│   │       ├── train.py
│   │       ├── predict.py
│   │       └── visualize.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Signup.tsx
│   │   │   ├── VerifyEmail.tsx
│   │   │   └── Modules.tsx
│   │   ├── App.tsx
│   │   ├── auth.tsx
│   │   ├── AuthCard.tsx
│   │   ├── api.ts
│   │   ├── data.ts
│   │   ├── nav.ts
│   │   ├── Shell.tsx
│   │   └── styles.css
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11
- Node.js and npm
- PostgreSQL
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/mimansa05/SubNexus-hackathon-odoo.git
cd SubNexus-hackathon-odoo
```

### 2. Backend Setup

```bash
cd backend

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file inside the `backend/` directory.

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/subnexus

JWT_SECRET=replace_with_a_secure_random_secret
JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
EMAIL_VERIFY_EXPIRE_HOURS=24

FRONTEND_URL=http://localhost:5173

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=SubNexus <no-reply@subnexus.local>
```

Replace the database credentials with your local PostgreSQL configuration.

Generate a secure JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Important:** Never commit `.env` files or expose JWT secrets, database passwords, or SMTP credentials.

When SMTP is not configured, the development email-verification link is printed in the backend console.

### 4. Start the Backend

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

- Backend: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Database health check: `http://127.0.0.1:8000/health/database`

Ensure that your PostgreSQL database has the schema required by the current application models before testing the APIs. Use the project's database initialization or migration workflow; do not drop existing tables to resolve schema mismatches.

### 5. Frontend Setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

### 6. Build the Frontend

```bash
cd frontend
npm run build
```

---

## Machine Learning Workflow

The churn prediction module is maintained separately under `backend/ml/`.

### Generate the Dataset

```bash
cd backend/ml
python src/generate_data.py
```

### Analyze the Dataset

```bash
python src/analyze_data.py
```

### Train the Model

```bash
python src/train.py
```

### Generate Visualizations

```bash
python src/visualize.py
```

### Run a Sample Prediction

```bash
python src/predict.py
```

The trained model is saved under `backend/ml/models/churn_model.pkl`. The FastAPI churn service loads this model for prediction.

---

## API Modules

The backend exposes REST endpoints grouped by functional domain.

| Module | Base path |
|---|---|
| Authentication | `/api/v1/auth` |
| Administration | `/api/v1/admin` |
| Customers | `/api/v1/customers` |
| Products | `/api/v1/products` |
| Plans | `/api/v1/plans` |
| Subscriptions | `/api/v1/subscriptions` |
| Quotations | `/api/v1/quotations` |
| Invoices | `/api/v1/invoices` |
| Payments | `/api/v1/payments` |
| Discounts | `/api/v1/discounts` |
| Reconciliation | `/api/v1/reconciliation` |
| Analytics | `/api/v1/analytics` |
| Churn prediction | `/api/v1/churn` |
| Approvals | `/api/v1/approvals` |
| Audit logs | `/api/v1/audit-logs` |
| Notifications | `/api/v1/notifications` |

For request parameters, response schemas, and interactive testing, visit the Swagger documentation at `/docs`.

---

## Security

SubNexus includes several security mechanisms:

- JWT-based authentication.
- Password hashing using Argon2.
- Email verification tokens.
- Role-based API authorization.
- Protected frontend routes.
- Input validation using Pydantic.
- Separate permissions for administrative and staff operations.
- Environment-based secret and database configuration.
- Audit logging for governance-related activities.

Frontend route visibility is not a substitute for backend authorization. Sensitive operations must always be protected by server-side permission checks.

---

## Current Implementation Notes

SubNexus is an actively developed hackathon prototype.

- The backend contains modular REST APIs for subscription, billing, payment, reconciliation, analytics, and governance operations.
- The frontend provides a dashboard and module-oriented workspace.
- Some frontend views currently use local demonstration data and are not yet connected to every backend endpoint.
- The churn model uses synthetic training data and needs validation on representative real-world customer data before production use.
- Payment gateway integrations and automated payment collection should only be considered operational when connected to an actual provider.
- The AI Assistant interface currently includes prototype interactions and example responses.

These distinctions help keep the project documentation transparent about implemented functionality versus future integration work.

---

## Future Enhancements

- Complete frontend-to-backend integration for every module.
- Automated recurring invoice generation.
- Production payment gateway integration.
- Automated payment retry and dunning workflows.
- Advanced bank reconciliation and matching strategies.
- Real-time revenue and subscription dashboards.
- Churn model validation with real customer datasets.
- Personalized retention recommendations.
- Explainable ML predictions.
- AI-assisted financial and subscription reporting.
- Automated notifications and scheduled workflows.
- Production deployment, monitoring, and testing.

---

## Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes.
4. Test the affected functionality.
5. Commit with a descriptive message.
6. Open a pull request with a clear explanation.

Example:

```bash
git checkout -b feature/your-feature

git add .

git commit -m "Add: your feature description"

git push origin feature/your-feature
```

Please avoid committing secrets, local virtual environments, generated caches, or unnecessary build files.

---

## Team & Repository

**Project:** SubNexus — AI-Powered Subscription Management & Revenue Intelligence

**Repository:** [mimansa05/SubNexus-hackathon-odoo](https://github.com/mimansa05/SubNexus-hackathon-odoo)

**Default branch:** `main`

---

<p align="center">
  <strong>SubNexus</strong><br/>
  <em>Bringing subscriptions, billing, and revenue intelligence together.</em>
</p>
