import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';
import KnowledgeBasePage from './pages/KnowledgeBasePage';
import AboutPage from './pages/AboutPage';
import { WorkflowProvider } from './context/WorkflowContext';
import './App.css';

function App() {
  return (
    <WorkflowProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </Layout>
      </Router>
    </WorkflowProvider>
  );
}

export default App;
