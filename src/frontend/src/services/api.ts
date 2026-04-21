const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export interface AzureServiceStatus {
  azure_openai: boolean;
  document_intelligence: boolean;
  ai_search: boolean;
  ai_foundry: boolean;
}

export interface OrchestratorConfig {
  orchestrator_type: 'sequential' | 'legacy';
  agent_service: 'agent-framework' | 'foundry';
  description: string;
  features: {
    agent_framework_workflows: boolean;
    foundry_agent_service: boolean;
    azure_ai_search_hosted_tool: boolean;
    streaming_support: boolean;
  };
}

export interface ProcessDocumentRequest {
  send_email: boolean;
  use_azure: boolean;
}

export const api = {
  healthCheck: async () => {
    return request<any>('/api/health');
  },

  getOrchestratorConfig: async (): Promise<OrchestratorConfig> => {
    return request<OrchestratorConfig>('/api/config/orchestrator');
  },

  getAzureStatus: async (): Promise<AzureServiceStatus> => {
    return request<AzureServiceStatus>('/api/azure/status');
  },

  uploadDocument: async (file: File, options: ProcessDocumentRequest) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('send_email', options.send_email.toString());
    formData.append('use_azure', options.use_azure.toString());

    return request<any>('/api/process/upload', {
      method: 'POST',
      body: formData,
    });
  },

  processSample: async (sampleName: string, options: ProcessDocumentRequest) => {
    return request<any>('/api/process/sample', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sample_name: sampleName, ...options }),
    });
  },

  getKnowledgeBase: async () => {
    return request<any>('/api/knowledge-base');
  },

  getExecutiveOrder: async (name: string) => {
    return request<any>(`/api/knowledge-base/executive-order/${encodeURIComponent(name)}`);
  },

  getSampleProposals: async () => {
    return request<any>('/api/knowledge-base/samples');
  },
};
