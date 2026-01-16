# Grant Compliance Frontend

React + TypeScript frontend for the Grant Proposal Compliance Automation system.

## Features

- 📄 Document upload and processing
- 📊 Interactive results dashboard with score explanations
- 📚 Knowledge base explorer
- ⚙️ Azure services configuration
- 🎨 Modern UI with Tailwind CSS

### Recent Updates (v2.0)

- **Score Explanations**: Interactive tooltips explain what each score means
- **Risk Score Breakdown**: Visual breakdown showing how risk is calculated from compliance, quality, and completeness
- **Full Analysis View**: Expandable sections to view complete AI summarization output
- **Assessment Certainty**: New metric showing how definitive the risk classification is
- **Improved Executive Order Display**: Shows EO numbers and sources instead of relevance percentages
- **Confidence Score Clarity**: Clear distinction between AI confidence (certainty) and compliance score (alignment)

## Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8000

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` if your backend runs on a different URL:

```
VITE_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Lint code

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   ├── pages/           # Page components
│   │   ├── UploadPage.tsx
│   │   ├── ResultsPage.tsx
│   │   ├── KnowledgeBasePage.tsx
│   │   └── AboutPage.tsx
│   ├── context/         # React context
│   │   └── WorkflowContext.tsx
│   ├── services/        # API services
│   │   └── api.ts
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML template
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Key Technologies

- **React 19.2.3** - UI framework (latest secure version, patched for CVE-2025-55182)
- **TypeScript 5.7.3** - Type safety
- **Vite 6.4.1** - Build tool
- **Tailwind CSS 3.4.19** - Styling
- **React Router 7.11.0** - Navigation
- **Axios 1.7.9** - HTTP client
- **Recharts** - Data visualization

## Security

### CVE-2025-55182 (React2Shell) Mitigation

This application has been upgraded to **React 19.2.3**, which includes security patches for CVE-2025-55182 (React2Shell vulnerability).

**Vulnerability Details:**
- **Affected Versions**: React 19.0.0, 19.1.0, 19.1.1, 19.2.0
- **Current Version**: React 19.2.3 ✅ (Patched and secure)
- **Status**: Fully compliant with Microsoft security guidance

**Architecture Security:**
- Client-side React SPA (not affected by React Server Components vulnerability)
- Separate FastAPI backend (no Next.js, no RSC)
- All dependencies audited: 0 vulnerabilities

For more information: [Microsoft Security Blog - CVE-2025-55182](https://msrc.microsoft.com/blog/2025/05/microsoft-security-response-center-react-cve-2025-55182/)

## Azure Integration

The frontend connects to Azure services through the FastAPI backend:

- **Azure AI Foundry / Agent Framework** - Agent orchestration (configurable via `AGENT_SERVICE`)
- **Azure OpenAI** - LLM analysis for compliance and summarization
- **Azure AI Search** - Semantic search for executive orders knowledge base
- **Azure Document Intelligence** - OCR and document text extraction

Toggle "Use Azure Services" in the sidebar to switch between Azure and demo mode.

### Understanding the Scores

The Results page displays several scores:

| Score | Description | Source |
|-------|-------------|--------|
| **Confidence Score** | AI's certainty about its analysis (0-100) | Compliance Agent |
| **Compliance Score** | How compliant the proposal is with executive orders (0-100) | Calculated from analysis status + findings |
| **Risk Score** | Composite risk assessment (0-100) | Risk Scoring Agent |
| **Assessment Certainty** | How definitive the risk classification is (0-100) | Risk Scoring Agent |

See [docs/ScoringSystem.md](../docs/ScoringSystem.md) for complete scoring documentation.

## Building for Production

```bash
npm run build
```

The build output will be in the `dist/` directory.

To preview the production build:

```bash
npm run preview
```

## Development Tips

- Hot reload is enabled - changes will reflect immediately
- TypeScript errors will show in the console
- Use React DevTools for debugging
- Check browser console for API errors

## API Integration

The frontend communicates with the backend through REST endpoints:

- `GET /api/health` - Health check
- `GET /api/azure/status` - Azure services status
- `POST /api/process/upload` - Upload and process document
- `POST /api/process/sample` - Process sample document
- `GET /api/knowledge-base` - Get knowledge base info
- `GET /api/knowledge-base/executive-order/{name}` - Get EO content
- `GET /api/knowledge-base/samples` - Get sample proposals

## Troubleshooting

### Port Already in Use

If port 3000 is in use, Vite will prompt you to use a different port.

### API Connection Error

- Ensure the backend is running on port 8000
- Check the `VITE_API_URL` in your `.env` file
- Verify CORS is configured correctly in the backend

### Build Errors

- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## Learn More

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Tailwind CSS](https://tailwindcss.com/docs)
