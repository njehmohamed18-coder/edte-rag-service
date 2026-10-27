# Enterprise Security & Architecture Policy

## 1. Billing Database Governance
The billing system (`urn:system:billing_db`) hosts critical financial tables including `urn:resource:billing_db:table:invoices`.
Strict access control policies apply to all operational roles.

## 2. Role Restrictions
Only authorized personnel assigned to `urn:role:finance_operator` may execute write operations on billing tables.
Interns must never modify invoice tables (`urn:resource:billing_db:table:invoices`) under any circumstances.
