# Grant Compliance Frontend

React + TypeScript frontend for the Grant Proposal Compliance Automation system.

## Features

- 📄 Document upload and processing
- 📊 Interactive results dashboard
- 📚 Knowledge base explorer
- ⚙️ Azure services configuration
- 🎨 Modern UI with Tailwind CSS

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

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - HTTP client
- **Recharts** - Data visualization

## Azure Integration

The frontend connects to Azure services through the FastAPI backend:

- Azure AI Foundry, Agent Framework - Agent orchestration
- Azure OpenAI - LLM analysis
- Azure AI Search - Semantic search
- Azure Document Intelligence - OCR processing

Toggle "Use Azure Services" in the sidebar to switch between Azure and demo mode.

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
