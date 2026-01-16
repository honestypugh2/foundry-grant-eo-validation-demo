import React from 'react';
import { useWorkflow } from '../context/WorkflowContext';
import { useNavigate } from 'react-router-dom';

const ResultsPage: React.FC = () => {
  const { results } = useWorkflow();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = React.useState('overview');

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <p className="text-blue-800">
            No results yet. Please upload and analyze a document first.
          </p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-azure-500 text-white rounded-lg hover:bg-azure-600"
          >
            Go to Upload
          </button>
        </div>
      </div>
    );
  }

  const { risk_report, compliance_report, summary, metadata } = results;

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-azure-700 mb-2">
          📊 Compliance Results Dashboard
        </h1>
        <p className="text-gray-600">
          Detailed analysis and risk assessment
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', label: '📊 Overview' },
            { id: 'summary', label: '📋 Summary' },
            { id: 'compliance', label: '✅ Compliance' },
            { id: 'risk', label: '⚠️ Risk Analysis' },
            { id: 'email', label: '📧 Email' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-azure-500 text-azure-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow">
        {activeTab === 'overview' && (
          <OverviewTab
            results={results}
            metadata={metadata}
            risk_report={risk_report}
            compliance_report={compliance_report}
          />
        )}
        {activeTab === 'summary' && (
          <SummaryTab summary={summary} metadata={metadata} />
        )}
        {activeTab === 'compliance' && (
          <ComplianceTab compliance_report={compliance_report} />
        )}
        {activeTab === 'risk' && <RiskTab risk_report={risk_report} compliance_report={compliance_report} />}
        {activeTab === 'email' && <EmailTab results={results} />}
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab: React.FC<any> = ({
  results,
  metadata,
  risk_report,
  compliance_report,
}) => {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6">Document Overview</h2>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <MetricCard
          label="Word Count"
          value={metadata?.word_count?.toLocaleString() || '0'}
        />
        <MetricCard label="Page Count" value={metadata?.page_count || '0'} />
        <MetricCard
          label="Risk Score"
          value={`${risk_report?.overall_score?.toFixed(1) || '0'}%`}
        />
        <MetricCard
          label="Compliance"
          value={`${compliance_report?.compliance_score?.toFixed(1) || '0'}%`}
        />
        <MetricCard
          label="Violations"
          value={compliance_report?.violations?.length || 0}
        />
      </div>

      {/* Score Explanations */}
      <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="text-md font-semibold mb-3 text-blue-900">📊 Understanding Your Scores</h3>
        <div className="space-y-2 text-sm text-blue-800">
          <div>
            <strong>Confidence Score ({compliance_report?.confidence_score?.toFixed(1) || '0'}%):</strong> Measures how certain the AI is about its analysis. 
            <span className="italic">
              {(compliance_report?.confidence_score || 0) >= 90 ? ' (Very reliable)' : 
               (compliance_report?.confidence_score || 0) >= 70 ? ' (Reliable)' : 
               (compliance_report?.confidence_score || 0) >= 50 ? ' (Manual review recommended)' : 
               ' (Expert review required)'}
            </span>
          </div>
          <div>
            <strong>Compliance Score ({compliance_report?.compliance_score?.toFixed(1) || '0'}%):</strong> Measures alignment with executive order requirements.
            <span className="italic">
              {(compliance_report?.compliance_score || 0) >= 90 ? ' (Excellent compliance)' : 
               (compliance_report?.compliance_score || 0) >= 70 ? ' (Good compliance)' : 
               (compliance_report?.compliance_score || 0) >= 50 ? ' (Needs attention)' : 
               ' (Significant issues)'}
            </span>
          </div>
          <div>
            <strong>Risk Score ({risk_report?.overall_score?.toFixed(1) || '0'}%):</strong> Overall risk assessment (higher = lower risk). 
            Calculated as: Compliance (60%) + Quality (25%) + Completeness (15%).
            <span className="italic">
              {(risk_report?.overall_score || 0) >= 90 ? ' → Recommend approval' : 
               (risk_report?.overall_score || 0) >= 75 ? ' → Approve with minor revisions' : 
               (risk_report?.overall_score || 0) >= 60 ? ' → Major revisions required' : 
               ' → Recommend rejection/rework'}
            </span>
          </div>
        </div>
        <p className="text-xs text-blue-700 mt-3 italic">See docs/ScoringSystem.md for complete documentation</p>
      </div>

      <div className="border-t pt-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-4">Overall Assessment</h3>
            <div className="space-y-2">
              <InfoRow
                label="Status"
                value={results.overall_status?.toUpperCase().replace('_', ' ')}
              />
              <InfoRow
                label="Risk Level"
                value={risk_report?.risk_level?.toUpperCase()}
              />
              <InfoRow
                label="Assessment Certainty"
                value={`${(risk_report?.assessment_certainty ?? risk_report?.confidence)?.toFixed(1) || '0'}%`}
              />
            </div>

            {risk_report?.requires_notification ? (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-yellow-800 font-medium">
                  ⚠️ Attorney review required
                </p>
              </div>
            ) : (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-800 font-medium">
                  ✅ No immediate concerns
                </p>
              </div>
            )}
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Processing Info</h3>
            <div className="space-y-2 text-sm text-gray-600">
              <p>
                <strong>File:</strong> {metadata?.file_name || 'Unknown'}
              </p>
              <p>
                <strong>Processed:</strong>{' '}
                {metadata?.processing_timestamp || 'N/A'}
              </p>
              <p>
                <strong>Method:</strong>{' '}
                {results.use_azure ? 'Azure' : 'Local'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Summary Tab Component
const SummaryTab: React.FC<any> = ({ summary }) => {
  // Handle different summary formats
  const executiveSummary = typeof summary === 'string' 
    ? summary 
    : summary?.executive_summary || summary?.summary || 'No summary available';
  
  // Get the full detailed analysis (complete AI output)
  const detailedAnalysis = typeof summary === 'string'
    ? null
    : summary?.detailed_analysis || null;
  
  const keyClauses = Array.isArray(summary?.key_clauses) 
    ? summary.key_clauses 
    : [];
  
  const keyTopics = Array.isArray(summary?.key_topics) 
    ? summary.key_topics 
    : [];

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6">Document Summary</h2>

      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-3">Executive Summary</h3>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
            {executiveSummary}
          </p>
        </div>
      </div>

      {/* Full Detailed Analysis - shows complete AI output */}
      {detailedAnalysis && detailedAnalysis !== executiveSummary && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-3">📄 Full Analysis</h3>
          <details className="cursor-pointer" open>
            <summary className="text-sm text-azure-600 hover:text-azure-700 font-medium mb-3">
              View complete summarization output
            </summary>
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 max-h-[600px] overflow-y-auto">
              <div className="text-gray-700 leading-relaxed whitespace-pre-wrap font-mono text-sm">
                {detailedAnalysis}
              </div>
            </div>
          </details>
        </div>
      )}

      <div className="border-t pt-6 mb-8">
        <h3 className="text-lg font-semibold mb-4">Key Clauses & Requirements</h3>
        {keyClauses.length > 0 ? (
          <div className="space-y-4">
            {keyClauses.map((clause: string, i: number) => (
              <div key={i} className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-800 mb-1">
                  Clause {i + 1}
                </p>
                <p className="text-gray-700 whitespace-pre-wrap">{clause}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No key clauses identified</p>
        )}
      </div>

      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-4">Key Topics Identified</h3>
        {keyTopics.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {keyTopics.map((topic: string, i: number) => (
              <span
                key={i}
                className="px-3 py-1 bg-azure-100 text-azure-700 rounded-full text-sm font-medium"
              >
                🏷️ {topic}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-500">No topics identified</p>
        )}
      </div>
    </div>
  );
};

// Compliance Tab Component
const ComplianceTab: React.FC<any> = ({ compliance_report }) => {
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6">Compliance Validation Results</h2>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <MetricCard
          label="Compliance Score"
          value={`${compliance_report?.compliance_score?.toFixed(1) || '0'}%`}
        />
        <MetricCard
          label="Status"
          value={
            compliance_report?.overall_status?.replace('_', ' ').toUpperCase() ||
            'UNKNOWN'
          }
        />
        <MetricCard
          label="Relevant EOs"
          value={compliance_report?.relevant_executive_orders?.length || 0}
        />
      </div>

      {/* Full Analysis with Citations */}
      {compliance_report?.analysis && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">📄 Detailed Compliance Analysis</h3>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed font-mono">
              {compliance_report.analysis}
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2 italic">
            * Analysis includes citations to specific sections of executive orders from the knowledge base
          </p>
          
          {/* Citation Details Section */}
          {compliance_report?.citations && compliance_report.citations.length > 0 && (
            <div className="mt-6">
              <h4 className="text-md font-semibold mb-3 text-azure-700">📎 Citation Details</h4>
              <div className="space-y-4">
                {compliance_report.citations.map((citation: any, idx: number) => (
                  <div key={idx} className="p-4 bg-white border-l-4 border-azure-500 rounded-lg shadow-sm">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h5 className="font-bold text-gray-900">{citation.title || `Citation ${idx + 1}`}</h5>
                        {citation.url && (
                          <a 
                            href={citation.url} 
                            className="text-xs text-azure-600 hover:text-azure-700 underline mt-1 block"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {citation.url}
                          </a>
                        )}
                      </div>
                      {citation.tool_name && (
                        <span className="ml-3 text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                          Tool: {citation.tool_name}
                        </span>
                      )}
                    </div>
                    
                    {citation.snippet && (
                      <div className="mt-3 p-3 bg-gray-50 rounded border border-gray-200">
                        <p className="text-xs font-semibold text-gray-600 mb-1">Excerpt:</p>
                        <p className="text-sm text-gray-700 italic">"{citation.snippet}"</p>
                      </div>
                    )}
                    
                    {citation.additional_properties && Object.keys(citation.additional_properties).length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-semibold text-gray-600 mb-2">Additional Properties:</p>
                        <div className="grid grid-cols-2 gap-2">
                          {Object.entries(citation.additional_properties).map(([key, value]: [string, any]) => (
                            <div key={key} className="text-xs">
                              <span className="font-medium text-gray-700">{key.replace(/_/g, ' ')}:</span>
                              <span className="text-gray-600 ml-1">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {citation.annotated_regions && citation.annotated_regions.length > 0 && (
                      <div className="mt-3">
                        <p className="text-xs font-semibold text-gray-600 mb-1">Text Regions:</p>
                        <div className="flex flex-wrap gap-2">
                          {citation.annotated_regions.map((region: any, regionIdx: number) => (
                            <span key={regionIdx} className="text-xs bg-azure-50 text-azure-700 px-2 py-1 rounded border border-azure-200">
                              {region.start_index} - {region.end_index}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {citation.file_id && (
                      <div className="mt-2 text-xs text-gray-500">
                        File ID: {citation.file_id}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="border-t pt-6 mb-8">
        <h3 className="text-lg font-semibold mb-4">📜 Referenced Executive Orders</h3>
        {compliance_report?.relevant_executive_orders?.length > 0 ? (
          <div className="space-y-4">
            {compliance_report.relevant_executive_orders.map(
              (eo: any, i: number) => (
                <div key={i} className="p-4 border-l-4 border-blue-500 bg-blue-50 rounded-r-lg shadow-sm">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-bold text-gray-900 text-base">
                        {eo.title || eo.name || `Executive Order ${eo.eo_number || eo.number}`}
                      </h4>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        EO {eo.eo_number || eo.number || 'N/A'}
                      </span>
                    </div>
                  </div>
                  {eo.source && (
                    <p className="text-xs text-gray-600 mb-2">
                      Source: {eo.source.replace(/_/g, ' ')}
                    </p>
                  )}
                  {eo.key_requirements?.length > 0 && (
                    <div className="mt-3 text-sm text-gray-700">
                      <strong className="text-gray-900">Key Requirements & Citations:</strong>
                      <div className="mt-2 space-y-2">
                        {eo.key_requirements.map((req: string, j: number) => (
                          <div key={j} className="pl-3 border-l-2 border-gray-300">
                            <p className="text-gray-700 italic">"{req.substring(0, 300)}{req.length > 300 ? '...' : ''}"</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            )}
          </div>
        ) : (
          <p className="text-gray-500">No relevant executive orders found</p>
        )}
      </div>

      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-4">Compliance Violations</h3>
        {compliance_report?.violations?.length > 0 ? (
          <div className="space-y-4">
            {compliance_report.violations.map((violation: any, i: number) => (
              <div key={i} className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="font-semibold text-red-800 mb-2">
                  Violation {i + 1}: {violation.message}
                </p>
                <p className="text-sm text-red-700">
                  EO: {violation.executive_order}
                </p>
                <p className="text-sm text-red-700 mt-1">
                  Requirement: {violation.requirement?.substring(0, 150)}...
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800 font-medium">
              ✅ No compliance violations found
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// Risk Tab Component
const RiskTab: React.FC<any> = ({ risk_report, compliance_report }) => {
  // Extract risk breakdown scores
  const riskBreakdown = risk_report?.risk_breakdown || {};
  const complianceRiskWeighted = riskBreakdown.compliance_risk?.score ?? 0;
  const qualityRisk = riskBreakdown.quality_risk?.score ?? 0;
  const completenessRisk = riskBreakdown.completeness_risk?.score ?? 0;
  
  // Get raw compliance score and confidence for transparency
  const rawComplianceScore = compliance_report?.compliance_score ?? 0;
  const aiConfidence = compliance_report?.confidence_score ?? 70;

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6">Risk Assessment</h2>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <MetricCard
          label="Overall Risk Score"
          value={`${risk_report?.overall_score?.toFixed(1) || '0'}%`}
          subtitle={risk_report?.risk_level?.toUpperCase()}
        />
        <MetricCard
          label="Assessment Certainty"
          value={`${(risk_report?.assessment_certainty ?? risk_report?.confidence)?.toFixed(1) || '0'}%`}
        />
        <MetricCard
          label="Notification Required"
          value={risk_report?.requires_notification ? 'Yes' : 'No'}
        />
      </div>

      {/* Risk Breakdown by Component */}
      <div className="mb-8 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <h3 className="text-md font-semibold mb-4 text-gray-800">📊 Risk Score Breakdown</h3>
        <p className="text-xs text-gray-600 mb-4">
          Formula: Risk = (Confidence-Weighted Compliance × 60%) + (Quality × 25%) + (Completeness × 15%)
        </p>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-white rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600 mb-1">Confidence-Weighted Compliance (60%)</p>
            <p className="text-xl font-bold text-gray-800">{complianceRiskWeighted.toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-1">= {rawComplianceScore.toFixed(0)}% × {aiConfidence.toFixed(0)}% confidence</p>
          </div>
          <div className="text-center p-3 bg-white rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600 mb-1">Quality (25%)</p>
            <p className="text-xl font-bold text-gray-800">{qualityRisk.toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-1">Document structure & clarity</p>
          </div>
          <div className="text-center p-3 bg-white rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600 mb-1">Completeness (15%)</p>
            <p className="text-xl font-bold text-gray-800">{completenessRisk.toFixed(1)}%</p>
            <p className="text-xs text-gray-500 mt-1">Required sections present</p>
          </div>
        </div>
        
        {/* Raw vs Weighted Compliance Explanation */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-blue-800">
            <strong>💡 Note:</strong> The Compliance Score from the Compliance tab ({rawComplianceScore.toFixed(1)}%) 
            is multiplied by AI Confidence ({aiConfidence.toFixed(1)}%) to produce the risk-weighted value ({complianceRiskWeighted.toFixed(1)}%). 
            Lower AI confidence reduces the weighted score to account for analysis uncertainty.
          </p>
        </div>
      </div>

      {risk_report?.risk_factors?.length > 0 && (
        <div className="border-t pt-6 mb-8">
          <h3 className="text-lg font-semibold mb-4">Risk Factors</h3>
          <div className="space-y-3">
            {risk_report.risk_factors.map((factor: any, i: number) => {
              const icon = factor.severity === 'high' ? '🔴' : '🟡';
              return (
                <div
                  key={i}
                  className="p-4 border border-gray-200 rounded-lg"
                >
                  <p className="font-semibold text-gray-800">
                    {icon} {factor.factor} ({factor.severity})
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {factor.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {risk_report?.recommendations?.length > 0 && (
        <div className="border-t pt-6 mb-8">
          <h3 className="text-lg font-semibold mb-4">Recommendations</h3>
          <div className="space-y-3">
            {risk_report.recommendations.map((rec: any, i: number) => (
              <div
                key={i}
                className={`p-4 rounded-lg ${
                  rec.priority === 'critical' || rec.priority === 'high'
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-blue-50 border border-blue-200'
                }`}
              >
                <p
                  className={`font-semibold ${
                    rec.priority === 'critical' || rec.priority === 'high'
                      ? 'text-red-800'
                      : 'text-blue-800'
                  }`}
                >
                  {rec.action}
                </p>
                <p
                  className={`text-sm mt-1 ${
                    rec.priority === 'critical' || rec.priority === 'high'
                      ? 'text-red-700'
                      : 'text-blue-700'
                  }`}
                >
                  {rec.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Referenced Executive Orders */}
      {risk_report?.relevant_executive_orders && risk_report.relevant_executive_orders.length > 0 && (
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">📜 Referenced Executive Orders</h3>
          <div className="space-y-4">
            {risk_report.relevant_executive_orders.map((eo: any, i: number) => (
              <div key={i} className="p-4 border-l-4 border-blue-500 bg-blue-50 rounded-r-lg shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-bold text-gray-900 text-base">
                      {eo.title || eo.name || `Executive Order ${eo.eo_number || eo.number}`}
                    </h4>
                  </div>
                  <div className="ml-4 flex-shrink-0">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      EO {eo.eo_number || eo.number || 'N/A'}
                    </span>
                  </div>
                </div>
                {eo.source && (
                  <p className="text-xs text-gray-600 mb-2">
                    Source: {eo.source.replace(/_/g, ' ')}
                  </p>
                )}
                {eo.key_requirements?.length > 0 && (
                  <div className="mt-3 text-sm text-gray-700">
                    <strong className="text-gray-900">Key Requirements & Citations:</strong>
                    <div className="mt-2 space-y-2">
                      {eo.key_requirements.map((req: string, j: number) => (
                        <div key={j} className="pl-3 border-l-2 border-gray-300">
                          <p className="text-gray-700 italic">"{req.substring(0, 300)}{req.length > 300 ? '...' : ''}"</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Email Tab Component
const EmailTab: React.FC<any> = ({ results }) => {
  if (!results.email_sent) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold mb-6">Email Notification</h2>
        <div className="p-6 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-800">
            Email notification was not sent for this proposal.
          </p>
          {!results.risk_report?.requires_notification && (
            <p className="text-blue-700 mt-2">
              ✅ Risk level does not require attorney notification
            </p>
          )}
        </div>
      </div>
    );
  }

  const emailData = results.steps?.notification?.email_data || {};
  const sendResult = results.steps?.notification?.send_result || {};

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-6">Email Notification</h2>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <div>
          <h3 className="text-lg font-semibold mb-3">Email Details</h3>
          <div className="space-y-2 text-sm">
            <InfoRow label="To" value={emailData.to || 'Unknown'} />
            <InfoRow label="From" value={emailData.from || 'Unknown'} />
            <InfoRow
              label="Priority"
              value={emailData.priority?.toUpperCase() || 'NORMAL'}
            />
            <InfoRow
              label="Status"
              value={sendResult.status?.toUpperCase() || 'UNKNOWN'}
            />
            <InfoRow label="Sent" value={sendResult.sent_at || 'Unknown'} />
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-3">Send Method</h3>
          {sendResult.method === 'graph_api' ? (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 font-medium">
                ✓ Sent via Microsoft Graph API
              </p>
            </div>
          ) : (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800 font-medium">
                🔧 Simulated (Demo Mode)
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="border-t pt-6 mb-6">
        <h3 className="text-lg font-semibold mb-3">Subject</h3>
        <div className="p-4 bg-gray-50 rounded-lg font-mono text-sm">
          {emailData.subject || 'No subject'}
        </div>
      </div>

      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-3">Email Body</h3>
        <details className="cursor-pointer">
          <summary className="text-sm text-azure-600 hover:text-azure-700 font-medium">
            View full email content
          </summary>
          <pre className="mt-4 p-4 bg-gray-50 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap">
            {emailData.body_text || 'No content'}
          </pre>
        </details>
      </div>
    </div>
  );
};

// Helper Components
const MetricCard: React.FC<{
  label: string;
  value: string | number;
  subtitle?: string;
}> = ({ label, value, subtitle }) => (
  <div className="bg-gray-50 p-4 rounded-lg text-center">
    <p className="text-sm text-gray-600 mb-1">{label}</p>
    <p className="text-2xl font-bold text-gray-800">{value}</p>
    {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
  </div>
);

const InfoRow: React.FC<{ label: string; value?: string }> = ({
  label,
  value,
}) => (
  <p className="text-sm">
    <span className="font-semibold text-gray-700">{label}:</span>{' '}
    <span className="text-gray-600">{value || 'N/A'}</span>
  </p>
);

export default ResultsPage;
