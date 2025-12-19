# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive security documentation for CVE-2025-55182 mitigation
- React 19.2.3 upgrade with full security patch compliance

### Changed
- Updated React from 18.3.1 to 19.2.3 (CVE-2025-55182 patched version)
- Updated React Router from 6.30.2 to 7.11.0 (React 19 compatible)
- Updated TypeScript from 5.3.3 to 5.7.3
- Updated all type definitions to React 19 (@types/react 19.0.6, @types/react-dom 19.0.3)
- Updated Azure SDK packages to latest versions
- Updated all build tools and dependencies to latest stable versions

### Security
- **CRITICAL**: Upgraded to React 19.2.3 to address CVE-2025-55182 (React2Shell vulnerability)
- Verified application architecture not vulnerable to React Server Components exploits
- All npm packages audited: 0 vulnerabilities
- Updated axios to 1.7.9 with security patches

## [2.0.0] - 2025-12-18

### Changed - Streamlit Migration to Async
- **BREAKING**: Migrated Streamlit app to use async processing
- Updated `streamlit_app.py` to use `asyncio.run()` with `process_grant_proposal_async()`
- Aligned Streamlit architecture with FastAPI async backend
- Removed legacy `streamlit_app.py` (mock data version)
- Renamed `streamlit_app_new.py` to `streamlit_app.py` as production version

### Added
- Streamlit async processing implementation
- `app/README.md` with comprehensive Streamlit documentation
- Deprecation warnings and migration guides
- Production-ready error handling in Streamlit app

### Improved
- Streamlit now uses real AgentOrchestrator instead of mock data
- Managed identity authentication by default in Streamlit
- Document Intelligence SDK integration in Streamlit
- Layout consistency between React and Streamlit interfaces

## [1.0.0] - 2025-11-15

### Added
- Initial release of Grant Proposal Compliance Automation system
- Multi-agent architecture with Azure AI Agent Framework
- React 18.2.0 frontend with TypeScript
- FastAPI backend with async processing
- Azure OpenAI integration for compliance analysis
- Azure AI Search integration for knowledge base
- Azure Document Intelligence for OCR processing
- Streamlit demo application
- Comprehensive documentation (Architecture, Deployment, User Guide)

### Features
- Document upload and processing
- Automated compliance analysis against executive orders
- Risk scoring system with three-dimensional assessment
- Knowledge base management
- Email notification system
- Human-in-the-loop validation workflow

### Azure Services
- Azure AI Foundry for agent orchestration
- Azure OpenAI Service for LLM analysis
- Azure AI Search for semantic search
- Azure Document Intelligence for document processing
- Azure Blob Storage for document management
- Azure Key Vault for secrets management
- Azure Monitor for observability

---

## Security Advisories

### CVE-2025-55182 (React2Shell) - December 2025
**Status**: ✅ PATCHED

**Affected Versions**: React 19.0.0, 19.1.0, 19.1.1, 19.2.0  
**Fixed In**: React 19.0.1, 19.1.2, 19.2.1+  
**Current Version**: React 19.2.3 ✅

**Details**: Critical vulnerability in React Server Components allowing remote code execution. This application:
- Uses React 19.2.3 (fully patched)
- Architecture: Client-side SPA + FastAPI backend (not affected by RSC vulnerability)
- No Next.js or React Server Components used
- Fully compliant with Microsoft security guidance

**References**:
- [Microsoft Security Response Center](https://msrc.microsoft.com/blog/2025/05/microsoft-security-response-center-react-cve-2025-55182/)
- [React Security Advisory](https://react.dev/blog/2025/05/react-security-update)

---

## Upgrade Notes

### Upgrading to React 19.2.3

**Breaking Changes from React 18:**
1. `ReactDOM.render()` deprecated → use `createRoot()`
2. Updated TypeScript types for `React.FC` and component props
3. Some lifecycle methods removed or updated
4. New ref and effect behavior

**Migration Steps:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm audit  # Should show 0 vulnerabilities
```

**Testing Checklist:**
- [ ] Run `npm run build` successfully
- [ ] Run `npm run dev` and test all routes
- [ ] Verify document upload functionality
- [ ] Check TypeScript compilation
- [ ] Test all user workflows

### Upgrading to Streamlit Async (v2.0.0)

**Breaking Changes:**
- Legacy `streamlit_app.py` removed
- Now uses `asyncio.run()` with async orchestrator
- Requires latest agent code changes

**Migration:**
- Use `streamlit_app.py` (production version)
- Update environment variables for managed identity
- Test async processing workflow

---

## Contributors

- Brittany Pugh (@honestypugh2)

---

**For questions or issues**, please open a GitHub issue or consult the documentation in `/docs/`.
