import React, { useEffect, useState } from 'react';
import { api, AzureServiceStatus, OrchestratorConfig } from '../services/api';
import { useWorkflow } from '../context/WorkflowContext';

const Header: React.FC = () => {
  const { useAzure } = useWorkflow();
  const [azureStatus, setAzureStatus] = useState<AzureServiceStatus | null>(null);
  const [orchestratorConfig, setOrchestratorConfig] = useState<OrchestratorConfig | null>(null);

  useEffect(() => {
    // Always fetch orchestrator config
    api.getOrchestratorConfig()
      .then(setOrchestratorConfig)
      .catch(console.error);
    
    if (useAzure) {
      api.getAzureStatus()
        .then(setAzureStatus)
        .catch(console.error);
    }
  }, [useAzure]);

  const configuredCount = azureStatus
    ? Object.values(azureStatus).filter(Boolean).length
    : 0;
  const totalServices = 4;

  return (
    <header className="bg-white shadow-sm px-6 py-4 border-b">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            Grant Proposal Compliance Demo
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Automated compliance checking with Azure AI
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Orchestrator type indicator */}
          {orchestratorConfig && (
            <div className="text-sm">
              <div className={`flex items-center space-x-2 ${
                orchestratorConfig.orchestrator_type === 'sequential' 
                  ? 'text-purple-600' 
                  : 'text-blue-600'
              }`}>
                <span className={`w-2 h-2 rounded-full ${
                  orchestratorConfig.orchestrator_type === 'sequential'
                    ? 'bg-purple-500'
                    : 'bg-blue-500'
                }`}></span>
                <span title={`Features: ${Object.entries(orchestratorConfig.features)
                  .filter(([_, v]) => v)
                  .map(([k]) => k.replace(/_/g, ' '))
                  .join(', ')}`}>
                  {orchestratorConfig.description}
                </span>
              </div>
            </div>
          )}
          
          {useAzure && azureStatus && (
            <div className="text-sm">
              {configuredCount === totalServices ? (
                <div className="flex items-center space-x-2 text-green-600">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span>All Azure services configured</span>
                </div>
              ) : configuredCount > 0 ? (
                <div className="flex items-center space-x-2 text-yellow-600">
                  <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
                  <span>
                    Partial configuration ({configuredCount}/{totalServices})
                  </span>
                </div>
              ) : (
                <div className="flex items-center space-x-2 text-red-600">
                  <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                  <span>No Azure services configured</span>
                </div>
              )}
            </div>
          )}
          {!useAzure && (
            <div className="flex items-center space-x-2 text-gray-600 text-sm">
              <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
              <span>Demo mode</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
