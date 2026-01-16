import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

interface ExecutiveOrder {
  name: string;
  type: string;
  eo_number?: string;
  category?: string;
}

interface KnowledgeBaseInfo {
  source: string;
  executive_orders_count: number;
  sample_proposals_count: number;
  executive_orders: ExecutiveOrder[] | string[]; // Support both formats
  sample_proposals: string[];
  index_name?: string;
}

const KnowledgeBasePage: React.FC = () => {
  const [kbInfo, setKbInfo] = useState<KnowledgeBaseInfo | null>(null);
  const [selectedEO, setSelectedEO] = useState<string>('');
  const [eoContent, setEoContent] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getKnowledgeBase()
      .then((data) => {
        setKbInfo(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error loading knowledge base:', error);
        setLoading(false);
      });
  }, []);

  const handleEOSelect = async (eoName: string) => {
    setSelectedEO(eoName);
    setEoContent(null);

    if (eoName) {
      try {
        const content = await api.getExecutiveOrder(eoName);
        setEoContent(content);
      } catch (error) {
        console.error('Error loading EO content:', error);
      }
    }
  };

  const handleDownloadPDF = async (eoName: string) => {
    try {
      // Create a download link
      const link = document.createElement('a');
      link.href = `/api/knowledge-base/download/${eoName}`;
      link.download = `${eoName}.pdf`;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download PDF. The file may not be available.');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-azure-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading knowledge base...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-azure-700 mb-2">
          📚 Knowledge Base Explorer
        </h1>
        <p className="text-gray-600">
          Browse executive orders and compliance guidelines
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">Executive Orders</h3>
          <p className="text-4xl font-bold text-azure-600">
            {kbInfo?.executive_orders_count || 0}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Available for compliance checking
          </p>
          {kbInfo?.source && (
            <p className="text-xs text-gray-400 mt-1">
              Source: {kbInfo.source === 'azure' ? '☁️ Azure AI Search' : '💾 Local Files'}
            </p>
          )}
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-2">Sample Proposals</h3>
          <p className="text-4xl font-bold text-azure-600">
            {kbInfo?.sample_proposals_count || 0}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Test documents for demo
          </p>
        </div>
      </div>

      {/* Executive Orders Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Executive Orders</h2>

        <select
          value={selectedEO}
          onChange={(e) => handleEOSelect(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent mb-6"
        >
          <option value="">-- Select an executive order --</option>
          {kbInfo?.executive_orders.map((eo) => {
            const eoName = typeof eo === 'string' ? eo : eo.name;
            const eoType = typeof eo === 'string' ? '' : eo.type;
            return (
              <option key={eoName} value={eoName}>
                {eoName.replace(/_/g, ' ')} {eoType === 'indexed' ? '(Azure)' : ''}
              </option>
            );
          })}
        </select>

        {eoContent && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {selectedEO.replace(/_/g, ' ')}
              </h3>
              <div className="flex items-center gap-3">
                {eoContent.word_count && (
                  <span className="text-sm text-gray-500">
                    {eoContent.word_count} words
                  </span>
                )}
                <button
                  onClick={() => handleDownloadPDF(selectedEO)}
                  className="flex items-center gap-2 px-4 py-2 bg-azure-500 text-white rounded-lg hover:bg-azure-600 transition-colors text-sm font-medium"
                >
                  <span>📥</span>
                  <span>Download PDF</span>
                </button>
              </div>
            </div>

            {eoContent.content ? (
              <details className="cursor-pointer" open={eoContent.type === 'indexed'}>
                <summary className="text-sm text-azure-600 hover:text-azure-700 font-medium mb-2">
                  View content {eoContent.source === 'azure' && <span className="text-xs text-gray-400">(from Azure AI Search)</span>}
                </summary>
                <div className="mt-4 p-4 bg-gray-50 rounded-lg max-h-96 overflow-y-auto">
                  <pre className="text-sm whitespace-pre-wrap text-gray-700">
                    {eoContent.content}
                  </pre>
                </div>
              </details>
            ) : (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800">
                  📄 PDF file - Download to view the full content
                </p>
                <p className="text-sm text-blue-600 mt-2">
                  {eoContent.message}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sample Proposals Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Sample Grant Proposals</h2>

        {kbInfo?.sample_proposals && kbInfo.sample_proposals.length > 0 ? (
          <div className="space-y-3">
            {kbInfo.sample_proposals.map((sample) => (
              <div
                key={sample}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">📄</span>
                  <span className="font-medium text-gray-800">{sample}</span>
                </div>
                <span className="text-sm text-gray-500">
                  {sample.endsWith('.pdf') ? 'PDF' : 'TXT'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No sample proposals found</p>
        )}
      </div>
    </div>
  );
};

export default KnowledgeBasePage;
