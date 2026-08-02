# Security Policy

Orchestrix AI is a portfolio demonstration. Do not use production credentials, regulated data, or confidential customer information.

## Implemented controls

- Typed workflow validation
- Node-count limits
- Explicit human approval state
- Versioned definitions
- Auditable actor and evidence records
- Environment-based API credentials
- No secrets committed to source control

## Production requirements

A production deployment would require authentication, RBAC, multi-tenant isolation, encrypted secret storage, database migrations, durable queues, idempotency, rate limiting, connector allowlists, prompt-injection defenses, audit retention, malware scanning, and security monitoring.
