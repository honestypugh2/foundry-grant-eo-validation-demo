import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useWorkflow } from '../context/WorkflowContext';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const { useAzure, setUseAzure } = useWorkflow();

  const navItems = [
    { path: '/', label: 'Upload & Analyze', icon: '📝' },
    { path: '/results', label: 'Results Dashboard', icon: '📊' },
    { path: '/knowledge-base', label: 'Knowledge Base', icon: '📚' },
    { path: '/about', label: 'About', icon: 'ℹ️' },
  ];

  return (
    <aside className="w-64 bg-white shadow-lg flex flex-col">
      <div className="p-6 border-b">
        <div className="flex items-center space-x-2 mb-2">
          <div className="w-8 h-8 bg-azure-500 rounded flex items-center justify-center text-white font-bold">
            A
          </div>
          <span className="font-bold text-lg text-gray-800">Azure AI</span>
        </div>
        <h1 className="text-sm font-semibold text-gray-600 mt-2">
          Grant Compliance
        </h1>
      </div>

      <div className="p-4 border-b">
        <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3">
          Configuration
        </h3>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={useAzure}
            onChange={(e) => setUseAzure(e.target.checked)}
            className="w-4 h-4 text-azure-500 border-gray-300 rounded focus:ring-azure-500"
          />
          <span className="text-sm text-gray-700">Use Azure Services</span>
        </label>
        {useAzure ? (
          <p className="text-xs text-green-600 mt-2">✓ Azure services enabled</p>
        ) : (
          <p className="text-xs text-gray-500 mt-2">🎬 Demo mode</p>
        )}
      </div>

      <nav className="flex-1 p-4">
        <h3 className="text-xs font-semibold text-gray-500 uppercase mb-3">
          Navigation
        </h3>
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-2 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? 'bg-azure-50 text-azure-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <span>{item.icon}</span>
                <span className="text-sm">{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t text-xs text-gray-500">
        <p>© 2025 Azure AI Demo</p>
        <p className="mt-1">Grant Compliance Automation</p>
      </div>
    </aside>
  );
};

export default Sidebar;
