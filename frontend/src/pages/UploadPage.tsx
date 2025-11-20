import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useWorkflow } from '../context/WorkflowContext';

const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { setResults, useAzure, setProcessing } = useWorkflow();
  const [file, setFile] = useState<File | null>(null);
  const [selectedSample, setSelectedSample] = useState<string>('');
  const [sendEmail, setSendEmail] = useState(true);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [samples, setSamples] = useState<string[]>([]);

  React.useEffect(() => {
    // Load sample proposals
    api.getSampleProposals()
      .then((data) => {
        setSamples(data.samples.map((s: any) => s.name));
      })
      .catch(console.error);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setSelectedSample('');
    }
  };

  const handleSampleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedSample(e.target.value);
    setFile(null);
  };

  const handleSubmit = async () => {
    if (!file && !selectedSample) {
      alert('Please select a file or sample proposal');
      return;
    }

    try {
      setProcessing(true);
      setProgress(10);
      setStatusMessage('Initializing AI agents...');

      let results;
      if (file) {
        setStatusMessage('Processing uploaded document...');
        setProgress(20);
        results = await api.uploadDocument(file, {
          send_email: sendEmail,
          use_azure: useAzure,
        });
      } else {
        setStatusMessage('Processing sample document...');
        setProgress(20);
        results = await api.processSample(selectedSample, {
          send_email: sendEmail,
          use_azure: useAzure,
        });
      }

      setProgress(100);
      setStatusMessage('Analysis complete!');
      setResults(results);

      // Navigate to results after a brief delay
      setTimeout(() => {
        navigate('/results');
      }, 1000);
    } catch (error: any) {
      console.error('Processing error:', error);
      alert(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setProcessing(false);
      setTimeout(() => {
        setProgress(0);
        setStatusMessage('');
      }, 2000);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-azure-700 mb-2">
          📝 Grant Proposal Upload & Analysis
        </h1>
        <p className="text-gray-600">
          Upload a grant proposal for automated compliance review
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Section */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Upload Document</h2>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer inline-flex items-center px-4 py-2 bg-azure-500 text-white rounded-lg hover:bg-azure-600 transition-colors"
              >
                Choose File
              </label>
              {file && (
                <p className="mt-4 text-sm text-gray-700">
                  Selected: <span className="font-medium">{file.name}</span>
                </p>
              )}
              <p className="text-xs text-gray-500 mt-2">
                Supported formats: PDF, Word, TXT
              </p>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Or Select a Sample</h2>
            <select
              value={selectedSample}
              onChange={handleSampleChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-azure-500 focus:border-transparent"
            >
              <option value="">-- Select a sample proposal --</option>
              {samples.map((sample) => (
                <option key={sample} value={sample}>
                  {sample}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Options Section */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Processing Options</h2>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={sendEmail}
                onChange={(e) => setSendEmail(e.target.checked)}
                className="w-4 h-4 text-azure-500 border-gray-300 rounded focus:ring-azure-500"
              />
              <span className="text-sm text-gray-700">
                Send email notification
              </span>
            </label>
            <p className="text-xs text-gray-500 mt-2">
              Email will be sent if risk threshold is exceeded
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Workflow Steps</h2>
            <ol className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <span className="mr-2">1.</span>
                <span>📄 <strong>Document Ingestion</strong> - Extract text</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">2.</span>
                <span>📋 <strong>Summarization</strong> - Generate summary</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">3.</span>
                <span>✅ <strong>Compliance Check</strong> - Validate EOs</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">4.</span>
                <span>⚠️ <strong>Risk Scoring</strong> - Calculate risk</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">5.</span>
                <span>📧 <strong>Email Notification</strong> - Alert if needed</span>
              </li>
            </ol>
          </div>
        </div>
      </div>

      {/* Process Button */}
      {(file || selectedSample) && (
        <div className="mt-6">
          <button
            onClick={handleSubmit}
            disabled={progress > 0}
            className="w-full lg:w-auto px-8 py-3 bg-azure-500 text-white font-semibold rounded-lg hover:bg-azure-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            🚀 Analyze for Compliance
          </button>
        </div>
      )}

      {/* Progress Indicator */}
      {progress > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <div className="mb-2 flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">
              {statusMessage}
            </span>
            <span className="text-sm text-gray-500">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-azure-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
