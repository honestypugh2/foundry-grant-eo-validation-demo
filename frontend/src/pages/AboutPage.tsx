import React from 'react';

const AboutPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-azure-700 mb-2">
          ℹ️ About This Demo
        </h1>
        <p className="text-gray-600">
          Grant Proposal Compliance Automation with Azure AI
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-8 space-y-8">
        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Overview
          </h2>
          <p className="text-gray-700 leading-relaxed">
            This solution accelerator demonstrates how to automate the review of
            grant proposals for compliance with executive orders using the 
            <strong> Azure AI Agent Framework</strong> and Azure AI services. 
            The system leverages specialized AI agents in a multi-agent orchestration 
            pattern to provide end-to-end automation from document ingestion through 
            risk assessment and notification.
          </p>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Features
          </h2>
          <ul className="space-y-3">
            {[
              {
                icon: '📄',
                title: 'Document Processing',
                desc: 'Automatic text extraction from PDF, Word, and text files',
              },
              {
                icon: '📋',
                title: 'AI Summarization',
                desc: 'Generate executive summaries and identify key clauses',
              },
              {
                icon: '✅',
                title: 'Compliance Validation',
                desc: 'Cross-check proposals against executive orders with precise citations',
              },
              {
                icon: '⚠️',
                title: 'Risk Assessment',
                desc: 'Calculate risk scores and identify compliance issues',
              },
              {
                icon: '📧',
                title: 'Email Notifications',
                desc: 'Automatic attorney notifications for high-risk proposals',
              },
              {
                icon: '👨‍⚖️',
                title: 'Human-in-the-Loop',
                desc: 'Attorney validation workflow for final approval',
              },
            ].map((feature, i) => (
              <li key={i} className="flex items-start space-x-3">
                <span className="text-2xl">{feature.icon}</span>
                <div>
                  <strong className="text-gray-800">{feature.title}:</strong>
                  <span className="text-gray-600"> {feature.desc}</span>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Technology Stack
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            {[
              { name: 'Azure AI Agent Framework', desc: 'Multi-agent orchestration & coordination' },
              { name: 'Azure AI Foundry', desc: 'Agent deployment & management' },
              { name: 'Azure OpenAI', desc: 'GPT-4 LLM analysis' },
              { name: 'Azure AI Search', desc: 'Semantic search & RAG' },
              { name: 'Document Intelligence', desc: 'OCR & document processing' },
              { name: 'React + TypeScript', desc: 'Modern UI framework' },
              { name: 'FastAPI', desc: 'REST backend API' },
              { name: 'Python Agent SDK', desc: 'Agent development framework' },
            ].map((tech, i) => (
              <div key={i} className="p-4 border border-gray-200 rounded-lg">
                <p className="font-semibold text-gray-800">{tech.name}</p>
                <p className="text-sm text-gray-600">{tech.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Workflow
          </h2>
          <ol className="space-y-3">
            {[
              'Upload Proposal → Document Ingestion Agent extracts text',
              'Summarization → Creates executive summary',
              'Compliance Check → Validates against executive orders',
              'Risk Scoring → Assigns compliance score',
              'Email Notification → Alerts attorney if needed',
              'Human Review → Attorney validates and approves',
            ].map((step, i) => (
              <li key={i} className="flex items-start">
                <span className="font-bold text-azure-600 mr-3">{i + 1}.</span>
                <span className="text-gray-700">{step}</span>
              </li>
            ))}
          </ol>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Multi-Agent Architecture
          </h2>
          <p className="text-gray-700 mb-4">
            Built with the <strong>Azure AI Agent Framework</strong>, this demo 
            showcases a coordinated multi-agent system where specialized agents 
            work together to automate grant compliance review:
          </p>
          <ul className="space-y-3">
            {[
              {
                name: 'Document Ingestion Agent',
                desc: 'OCR and text extraction from uploaded files',
              },
              {
                name: 'Summarization Agent',
                desc: 'Content analysis and executive summary generation',
              },
              {
                name: 'Compliance Validator Agent',
                desc: 'Executive order matching with citation tracking',
              },
              {
                name: 'Risk Scoring Agent',
                desc: 'Compliance risk assessment and scoring',
              },
              {
                name: 'Email Trigger Agent',
                desc: 'Intelligent notification management',
              },
            ].map((agent, i) => (
              <li key={i} className="flex items-start">
                <span className="text-azure-600 mr-2 font-bold">•</span>
                <div>
                  <span className="font-semibold text-gray-800">{agent.name}:</span>
                  <span className="text-gray-700"> {agent.desc}</span>
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-4 p-4 bg-azure-50 border border-azure-200 rounded-lg">
            <p className="text-sm text-gray-700">
              <strong>Agent Framework Benefits:</strong> Modular design, independent 
              scaling, specialized task handling, and coordinated workflows through 
              the orchestrator pattern.
            </p>
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Configuration
          </h2>
          <p className="text-gray-700 mb-3">
            Toggle "Use Azure Services" in the sidebar to switch between:
          </p>
          <div className="space-y-3">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="font-semibold text-green-800">Azure Mode</p>
              <p className="text-sm text-green-700">
                Full integration with Azure AI services
              </p>
            </div>
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="font-semibold text-blue-800">Demo Mode</p>
              <p className="text-sm text-blue-700">
                Local processing for quick testing
              </p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Learn More
          </h2>
          <div className="space-y-2">
            <a
              href="https://learn.microsoft.com/azure/ai-studio/how-to/develop/create-agent"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-azure-600 hover:text-azure-700"
            >
              → Azure AI Agent Framework Documentation
            </a>
            <a
              href="https://learn.microsoft.com/azure/ai-studio/"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-azure-600 hover:text-azure-700"
            >
              → Azure AI Foundry Documentation
            </a>
            <a
              href="https://github.com/your-org/grant-compliance-demo"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-azure-600 hover:text-azure-700"
            >
              → Project Repository
            </a>
            <a
              href="https://learn.microsoft.com/azure/ai-services/"
              target="_blank"
              rel="noopener noreferrer"
              className="block text-azure-600 hover:text-azure-700"
            >
              → Azure AI Services
            </a>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AboutPage;
