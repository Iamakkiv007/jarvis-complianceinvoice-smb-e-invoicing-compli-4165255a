# ComplianceInvoice — SMB e-Invoicing Compliance SaaS for Multi-Country Mandates

**Automate e-invoicing compliance across multiple countries. Reduce audit risk. Simplify global invoicing.**

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Supported Countries & Mandates](#supported-countries--mandates)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Compliance Standards](#compliance-standards)
- [Security & Data Privacy](#security--data-privacy)
- [Pricing](#pricing)
- [Support & Documentation](#support--documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**ComplianceInvoice** is a purpose-built SaaS platform designed for small and medium-sized businesses (SMBs) operating across multiple jurisdictions. We automate the complex, evolving requirements of e-invoicing mandates—from EU VAT compliance (e-invoicing directives) to emerging requirements in Asia-Pacific and the Americas.

### Why ComplianceInvoice?

- **Multi-Country Coverage**: Stay compliant with mandates in 40+ countries without maintaining separate systems
- **Automated Compliance**: Real-time validation against current regional requirements
- **Reduced Audit Risk**: Built-in audit trails, digital signatures, and archival compliance
- **Easy Integration**: REST API, native connectors, and middleware compatibility
- **Cost-Effective**: Flat-rate pricing—no per-invoice transaction fees
- **Regulatory Updates**: Automatic updates as tax/compliance rules change

---

## Key Features

### 1. **Universal Invoice Format Conversion**
   - Convert invoices to country-specific formats (UBL-2.3, EN 16931, ZUGFeRD, Facturae, etc.)
   - Auto-detect required format based on destination country
   - Support for multiple input formats (PDF, XML, JSON, CSV)

### 2. **Automated Compliance Validation**
   - Real-time validation of invoice content against regional requirements
   - Tax ID format verification
   - Mandatory field enforcement
   - Currency and date format normalization
   - Duplicate invoice detection

### 3. **Digital Signature & Encryption**
   - EU-compliant qualified electronic signatures (QES)
   - XAdES and CAdES support
   - End-to-end encryption for sensitive data
   - Timestamp authority integration

### 4. **Integration & Routing**
   - Direct connectivity to government e-invoicing portals
   - SaaS provider integration (Stripe, QuickBooks, SAP, NetSuite)
   - SFTP, email, and webhook delivery options
   - Batch processing for high-volume invoicing

### 5. **Audit Trail & Archival**
   - Immutable transaction logs compliant with regional record-keeping laws
   - 7-10 year archival retention (configurable)
   - Tamper-proof PDF generation with metadata
   - Real-time audit reports

### 6. **Multi-Language & Multi-Currency**
   - 25+ language support
   - Real-time currency conversion and reporting
   - Localized tax calculations
   - Regional payment term standards

### 7. **Dashboard & Analytics**
   - Submission status tracking (delivered, rejected, pending)
   - Compliance health score
   - Invoice volume and VAT analytics
   - Rejection reason analysis and remediation suggestions

---

## Supported Countries & Mandates

| Country | Mandate | Status | Format |
|---------|---------|--------|--------|
| **Austria** | e-invoicing requirement (B2B) | Active | UBL-2.3 / EN 16931 |
| **Belgium** | PEPPOL network requirement | Active | UBL-2.3 |
| **Czech Republic** | EET (EK system) | Active | Proprietary XML |
| **Denmark** | OIOUBL (Offentlig Information Online UBL) | Active | UBL-2.3 |
| **France** | CHORUS Pro (B2G) | Active | UBL-2.3 |
| **Germany** | ZUGFeRD, XRechnung | Active | ZUGFeRD 2.0 / XRechnung 3.0 |
| **Greece** | AADE MyData | Active | Greek Format |
| **Hungary** | Online Invoice System (OIS) | Active | XML |
| **Italy** | Sistema di Interscambio (SDI) | Active | UBL-2.3 |
| **Netherlands** | PEPPOL / UBL-2.3 | Active | UBL-2.3 |
| **Poland** | JPK_FA (VAT invoice register) | Active | XML |
| **Portugal** | SAF-T (Standard Audit File) | Active | SAF-T XML |
| **Romania** | e-Invoice System | Active | UBL-2.3 |
| **Spain** | Facturae, LROE | Active | Facturae 3.2 / UBL-2.3 |
| **Sweden** | e-invoicing requirement (B2B) | Active | UBL-2.3 |
| **United Kingdom** | Making Tax Digital (MTD) | Active | JSON/CSV |
| **Mexico** | CFDI (Comprobante Fiscal Digital por Internet) | Active | CFDI 4.0 |
| **Brazil** | NF-e, NFS-e | Active | Brazilian XML |
| **India** | GST e-Invoice, e-Waybill | Active | IRP Format |
| **Singapore** | PEPPOL network requirement | Active | UBL-2.3 |
| **Australia** | Voluntary e-invoicing | Planned | UBL-2.3 |

**Note**: Coverage expanding quarterly. [Check our roadmap](https://complianceinvoice.io/roadmap).

---

## Getting Started

### Prerequisites

- Active ComplianceInvoice SaaS account ([sign up free](https://complianceinvoice.io/signup))
- API key or OAuth credentials
- Integration environment (REST client, accounting software, or custom application)

### Quick Start (5 Minutes)

1. **Sign Up**: Create account at [complianceinvoice.io](https://complianceinvoice.io)
2. **Get API Key**: Available in [Dashboard → Settings → API Keys](https://app.complianceinvoice.io/settings/api-keys)
3. **Create Invoice**: POST to `/api/v1/invoices` with invoice data
4. **Validate**: System auto-validates against destination country rules
5. **Submit**: Auto-route or manually submit to relevant e-invoicing portal

### Example Request

curl -X POST https://api.complianceinvoice.io/v1/invoices \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15",
    "supplier": {
      "name": "Acme Corp",
      "tax_id": "DE123456789",
      "country": "DE"
    },
    "customer": {
      "name": "Client Ltd",
      "tax_id": "IT98765432",
      "country": "IT"
    },
    "total_amount": 1000.00,
    "currency": "EUR",
    "destination_country": "IT"
  }'

---

## Installation

### Via SaaS (Recommended)

No installation required—use [app.complianceinvoice.io](https://app.complianceinvoice.io).

### Self-Hosted (Enterprise)

# Clone repository
git clone https://github.com/complianceinvoice/core.git
cd complianceinvoice

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with database, secrets, etc.

# Run migrations
npm run migrate

# Start server
npm run start

### Docker Deployment

docker pull complianceinvoice/core:latest
docker run -e DATABASE_URL=postgresql://... -p 3000:3000 complianceinvoice/core:latest

---

## Configuration

### 1. **Organization Settings**

Set in Dashboard → Settings → Organization:

{
  "organization_name": "Your Company",
  "registration_country": "DE",
  "tax_id": "DE123456789",
  "default_currency": "EUR",
  "legal_entity_type": "GmbH"
}

### 2. **Compliance Rules**

Customize validation per country:

{
  "countries": {
    "IT": {
      "mandatory_fields": ["invoice_number", "invoice_date", "tax_id"],
      "validation_rules": "SDI",
      "auto_submit": true,
      "digital_signature_required": true
    }
  }
}

### 3. **Integration Connectors**

Configure in Dashboard → Integrations:

- **Accounting Software**: QuickBooks, Xero, SAP, NetSuite
- **Payment Gateways**: Stripe, PayPal
- **E-invoicing Portals**: Government PEPPOL nodes, national systems
- **Storage**: AWS S3, Azure Blob, Google Cloud Storage
- **Webhooks**: Custom endpoints for real-time notifications

### 4. **API Authentication**

Use Bearer token authentication:

Authorization: Bearer sk_live_xxxxxxxxxx

Or OAuth 2.0 for third-party integrations.

---

## Usage

### Creating an Invoice

const ComplianceInvoice = require('complianceinvoice');

const client = new ComplianceInvoice.Client({
  apiKey: process.env.COMPLIANCEINVOICE_API_KEY
});

const invoice = await client.invoices.create({
  invoice_number: 'INV-2024-001',
  invoice_date: '2024-01-15',
  due_date: '2024-02-14',
  supplier: {
    name: 'Your Company',
    address: '123 Main St',
    city: 'Berlin',
    postal_code: '10115',
    country: 'DE',
    tax_id: 'DE123456789'
  },
  customer: {
    name: 'Client Company',
    address: '456 Oak Ave',
    city: 'Rome',
    postal_code: '00100',
    country: 'IT',
    tax_id: 'IT98765432'
  },
  line_items: [
    {
      description: 'Consulting Services',
      quantity: 10,
      unit_price: 100.00,
      vat_rate: 19.0
    }
  ],
  total_amount: 1190.00,
  currency: 'EUR'
});

console.log(invoice.status); // 'validated'

### Submitting to Portal

// Auto-route to appropriate portal
const submission = await client.invoices.submit(invoice.id, {
  auto_route: true
});

// Or manually specify destination
const submission = await client.invoices.submit(invoice.id, {
  destination_portal: 'SDI', // Italy's Sistema di Interscambio
  delivery_method: 'API'
});

### Checking Status

const status = await client.invoices.getStatus(invoice.id);
console.log(status);
// {
//   "status": "delivered",
//   "submission_time": "2024-01-15T10:30:00Z",
//   "delivery_time": "2024-01-15T10:35:00Z",
//   "portal_reference": "IT2024001"
// }

### Bulk Processing

const bulkJob = await client.invoices.bulkCreate({
  source: 's3://bucket/invoices.csv',
  format: 'csv',
  mapping: {
    invoice_number: 'col_0',
    invoice_date: 'col_1',
    // ... field mappings
  },
  auto_validate: true,
  auto_submit: true
});

// Monitor progress
const progress = await client.jobs.getProgress(bulkJob.id);

---

## API Reference

### Base URL

**Production**: `https://api.complianceinvoice.io/v1`  
**Sandbox**: `https://sandbox-api.complianceinvoice.io/v1`

### Endpoints

#### Invoices

- `POST /invoices` — Create invoice
- `GET /invoices/{id}` — Retrieve invoice
- `PUT /invoices/{id}` — Update invoice
- `DELETE /invoices/{id}` — Delete invoice
- `GET /invoices` — List invoices (paginated)
- `POST /invoices/{id}/validate` — Validate against rules
- `POST /invoices/{id}/submit` — Submit to portal
- `GET /invoices/{id}/status` — Get submission status
- `GET /invoices/{id}/audit-trail` — View audit log

#### Validation

- `POST /validate` — Validate invoice payload
- `GET /validation-rules/{country}` — Get country rules

#### Compliance

- `GET /compliance/status` — Overall compliance dashboard
- `GET /compliance/audit-report` — Generate audit report
- `GET /compliance/rejections` — List rejected invoices

#### Webhooks

- `POST /webhooks` — Register webhook
- `GET /webhooks` — List webhooks
- `PUT /webhooks/{id}` — Update webhook
- `DELETE /webhooks/{id}` — Remove webhook

### Webhook Events

- `invoice.created`
- `invoice.validated`
- `invoice.submitted`
- `invoice.delivered`
- `invoice.rejected`
- `invoice.archived`

### Rate Limiting

- **Free Tier**: 100 requests/hour
- **Pro**: Unlimited
- **Enterprise**: Custom

Rate limit headers:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705334400

---

## Compliance Standards

ComplianceInvoice adheres to and implements the following standards:

### EU Directives

- **Directive 2014/55/EU** — Public Procurement e-Invoicing
- **Directive 2010/45/EU** (amended by 2013/42/EU) — VAT e-invoicing rules
- **Directive (EU) 2019/1024** — Open Data Directive

### Technical Standards

- **EN 16931:2017** — Universal business language for e-invoicing
- **UBL 2.3** — OASIS Universal Business Language
- **PEPPOL (Pan-European Public Procurement On-Line)** — Cross-border e-invoicing network
- **eIDAS (Regulation EU 910/2014)** — Digital signatures and trust services
- **XAdES/CAdES** — Qualified electronic signature formats

### Regional Formats

- **ZUGFeRD 2.0** (Germany)
- **XRechnung 3.0** (Germany)
- **Facturae 3.2** (Spain)
- **CFDI 4.0** (Mexico)
- **GST e-Invoice** (India)
- **NF-e** (Brazil)

### Data Protection

- **GDPR** — EU General Data Protection Regulation compliance
- **CCPA** — California Consumer Privacy Act
- **ISO 27001** — Information security certification

---

## Security & Data Privacy

### Data Protection

- **Encryption at Rest**: AES-256 encryption for all stored data
- **Encryption in Transit**: TLS 1.3 for all API communications
- **Zero-Knowledge Architecture**: We cannot access decrypted invoice content
- **Data Centers**: EU (Frankfurt) and US (Virginia) with automatic failover

### Compliance Certifications

- ✅ **ISO 27001:2013** — Information Security Management
- ✅ **SOC 2 Type II** — System Organization Controls
- ✅ **GDPR Compliant** — Full GDPR compliance
- ✅ **EU Cloud Code of Conduct** — Cloud provider standards

### Audit & Logging

- All API requests logged (30-day retention in logs, long-term in cold storage)
- Digital signatures on all submissions (immutable proof)
- Automated compliance aud