# Security Posture

**Last Updated**: November 2025  
**Status**: Production-Hardened (A Grade)  
**Audits**: 3 independent GPT-5 Pro security reviews

---

## Current Security Status

**Grade**: **A** (Production-Ready)

**Independent Audits**: 3 rounds of GPT-5 Pro security reviews (November 2025)
- **Findings**: 14 critical (P0) security issues identified
- **Fixed**: 14 (100%)  
- **Time**: 6 days from first audit to all fixes deployed

**See**: [ENGINEERING_OVERVIEW.md](../ENGINEERING_OVERVIEW.md) - Security Model section for complete technical details

---

## Security Features Implemented

### XSS Prevention ✅
- **SafeLink component**: Blocks `javascript:`, `data:`, `file:` URL schemes
- **Enforcement**: 100% of external data-driven URLs use SafeLink
- **React escaping**: All dynamic content uses `{variable}` syntax (auto-escaped)
- **CSP headers**: Content-Security-Policy enforced (production-strict)

### Authentication & Authorization ✅
- **Admin API key**: Constant-time comparison (`secrets.compare_digest`)
- **Rate limiting**: 10/min, 50/hour for admin endpoints (key-aware)
- **Audit logging**: All admin actions logged with timestamps, IP, key hash
- **No default keys**: Startup fails if `ADMIN_API_KEY` not set

### Injection Prevention ✅
- **SQL Injection**: SQLAlchemy ORM with parameterized queries
- **CSV Injection**: Formula character escaping (`=+-@|` prefixed with `'`)
- **Input validation**: Pydantic models, regex whitelists on query params

### Infrastructure Security ✅
- **Docker**: Non-root user (`appuser`), multi-stage build
- **Secrets**: No defaults, no commits, environment variables only
- **CORS**: Strict origin list, credentials disabled
- **Dependencies**: Dependabot enabled, CodeQL security scanning

### Monitoring & Response ✅
- **Sentry**: Full-stack error tracking (PII-scrubbed, GDPR-compliant)
- **Health checks**: `/healthz` tests DB + Redis connectivity
- **Audit logs**: PostgreSQL table tracking all admin actions
- **Mean time to fix**: <30 minutes (Sentry → fix → deploy)

---

## Security Audit History

### Round 1 (November 1, 2025) - Initial Audit
**Findings**: 4 critical (P0)
1. ✅ Sentry PII leakage (`sendDefaultPii: true`)
2. ✅ Debug endpoint exposure (`/debug/cors` public)
3. ✅ Default admin key (`change-me-in-production`)
4. ✅ Auth header mismatch (Bearer vs X-API-Key)

### Round 2 (November 5, 2025) - Deep Dive
**Findings**: 4 critical (P0)
1. ✅ Auth timing attack (string comparison)
2. ✅ XSS via `javascript:` URLs
3. ✅ CSV formula injection
4. ✅ Dedup race condition

### Round 3 (November 6, 2025) - Verification
**Findings**: 6 issues (enforcement & consistency)
1. ✅ SafeLink not enforced everywhere
2. ✅ Duplicate CSP headers
3. ✅ CSP production gating
4. ✅ /healthz missing
5. ✅ Migration safety guards
6. ✅ Audit logging infrastructure

**All findings addressed** ✅

---

## Reporting Vulnerabilities

**DO NOT create public GitHub issues for security vulnerabilities.**

**Email**: security@agi-tracker.app (or use GitHub Security tab)

**Response Time**: <48 hours  
**Disclosure Window**: 90 days coordinated disclosure

**See**: `.github/SECURITY.md` for complete disclosure policy

---

## Recent Security Improvements (November 2025)

**November 1-6**:
- SafeLink component (XSS prevention)
- CSP headers (production-strict, dev-relaxed)
- Auth timing-safe (constant-time comparison)
- Audit logging (all admin actions tracked)
- Docker non-root user + multi-stage
- UNIQUE constraints (race condition prevention)
- CSV sanitizer (centralized + tested)
- /healthz endpoint (dependency monitoring)

**Testing**:
- Blocking security tests in CI
- 15 CSV injection test cases
- CodeQL weekly scans
- Manual penetration testing

---

## Security Compliance

**Data Privacy**: ✅ GDPR Compliant
- No user PII collected
- Sentry configured with PII scrubbing (`sendDefaultPii: false`)
- All data from public sources (arXiv, company blogs)

**License**: CC BY 4.0 (data), MIT (code)

---

## For Complete Technical Details

**See**: [ENGINEERING_OVERVIEW.md](../ENGINEERING_OVERVIEW.md)
- Security Model section
- Authentication & Authorization
- XSS Prevention mechanisms
- Audit logging architecture
- Secrets management

**Historical audits**: `docs/archived/SECURITY_AUDIT_HISTORICAL.md`

---

**Last reviewed**: November 6, 2025  
**Next review**: Quarterly (or after major changes)  
**Status**: Production-ready, independently verified ✅
