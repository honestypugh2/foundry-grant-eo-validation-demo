import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AzureServiceStatus {
  azure_openai: boolean;
  document_intelligence: boolean;
  ai_search: boolean;
  ai_foundry: boolean;
}

export interface ProcessDocumentRequest {
  send_email: boolean;
  use_azure: boolean;
}

export const api = {
  // Health check
  healthCheck: async () => {
    const response = await apiClient.get('/api/health');
    return response.data;
  },

  // Azure services status
  getAzureStatus: async (): Promise<AzureServiceStatus> => {
    const response = await apiClient.get('/api/azure/status');
    return response.data;
  },

  // Upload and process document
  uploadDocument: async (file: File, options: ProcessDocumentRequest) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('send_email', options.send_email.toString());
    formData.append('use_azure', options.use_azure.toString());

    const response = await apiClient.post('/api/process/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Process sample document
  processSample: async (sampleName: string, options: ProcessDocumentRequest) => {
    const response = await apiClient.post('/api/process/sample', {
      sample_name: sampleName,
      ...options,
    });
    return response.data;
  },

  // Get knowledge base info
  getKnowledgeBase: async () => {
    const response = await apiClient.get('/api/knowledge-base');
    return response.data;
  },

  // Get executive order content
  getExecutiveOrder: async (name: string) => {
    const response = await apiClient.get(`/api/knowledge-base/executive-order/${name}`);
    return response.data;
  },

  // Get sample proposals
  getSampleProposals: async () => {
    const response = await apiClient.get('/api/knowledge-base/samples');
    return response.data;
  },
};

export default apiClient;
