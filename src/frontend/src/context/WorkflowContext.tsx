import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface WorkflowResults {
  status: string;
  document_data?: any;
  metadata?: any;
  summary?: any;
  compliance_report?: any;
  risk_report?: any;
  email_sent?: boolean;
  overall_status?: string;
  steps?: any;
}

interface WorkflowContextType {
  results: WorkflowResults | null;
  setResults: (results: WorkflowResults | null) => void;
  useAzure: boolean;
  setUseAzure: (use: boolean) => void;
  processing: boolean;
  setProcessing: (processing: boolean) => void;
}

const WorkflowContext = createContext<WorkflowContextType | undefined>(undefined);

export const WorkflowProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [results, setResults] = useState<WorkflowResults | null>(null);
  const [useAzure, setUseAzure] = useState(true);
  const [processing, setProcessing] = useState(false);

  return (
    <WorkflowContext.Provider
      value={{
        results,
        setResults,
        useAzure,
        setUseAzure,
        processing,
        setProcessing,
      }}
    >
      {children}
    </WorkflowContext.Provider>
  );
};

export const useWorkflow = (): WorkflowContextType => {
  const context = useContext(WorkflowContext);
  if (!context) {
    throw new Error('useWorkflow must be used within WorkflowProvider');
  }
  return context;
};
