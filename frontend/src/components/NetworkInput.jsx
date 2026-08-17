import { Terminal, Send, Server, Globe, Cpu, Activity, Zap, Network } from 'lucide-react';
import { useState } from 'react';
import { motion } from 'framer-motion';

const EXAMPLE_INTENTS = [
  "Configure VLAN 20 on distribution-sw-01",
  "Troubleshoot OSPF neighbor down on core-router-01",
  "Audit security compliance across all devices",
  "Generate a report on network health and compliance",
  "Monitor edge-router-01 CPU and memory",
  "Undo yesterday's VLAN changes on access-sw-01",
];

const NetworkInput = ({ onStart, isLoading }) => {
  const [intent, setIntent] = useState('');
  const [environment, setEnvironment] = useState('devnet-sandbox');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (intent.trim() && !isLoading) {
      onStart(intent.trim(), environment, `session-${Date.now()}`, 'engineer');
    }
  };

  return (
    <div className="card p-6 sm:p-8">
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[rgba(99,102,241,0.1)] border border-[rgba(99,102,241,0.15)] text-xs text-[#818cf8] font-medium mb-3">
          <Zap className="w-3.5 h-3.5" />
          Network Automation Assistant
        </div>
        <p className="text-sm text-[#94a3b8]">
          12 specialized agents &middot; 7 tools &middot; Memory &middot; Human approval &middot; RBAC
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="flex flex-wrap gap-2 mb-4">
          {EXAMPLE_INTENTS.map((ex, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setIntent(ex)}
              className="px-3 py-1.5 rounded-full text-xs font-medium
                       bg-[rgba(99,102,241,0.06)] border border-[rgba(99,102,241,0.1)]
                       text-[#94a3b8] hover:text-[#e2e8f0] hover:border-[rgba(99,102,241,0.25)]
                       hover:bg-[rgba(99,102,241,0.1)] transition-all duration-200"
            >
              {ex.length > 35 ? ex.slice(0, 35) + '...' : ex}
            </button>
          ))}
        </div>

        <div className="relative flex items-center gap-3">
          <div className="relative flex-1">
            <Terminal className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#64748b]" />
            <input
              type="text"
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder='e.g., "Configure VLAN 20 on distribution-sw-01"'
              className="input pl-12 pr-4 py-3.5 text-sm"
              disabled={isLoading}
            />
          </div>

          <select
            value={environment}
            onChange={(e) => setEnvironment(e.target.value)}
            className="input w-auto min-w-[140px] py-3.5 text-sm"
            disabled={isLoading}
          >
            <option value="devnet-sandbox">DevNet Sandbox</option>
            <option value="containerlab">ContainerLab</option>
            <option value="gns3">GNS3</option>
            <option value="eve-ng">EVE-NG</option>
          </select>

          <motion.button
            whileHover={!isLoading && intent.trim() ? { scale: 1.02 } : {}}
            whileTap={!isLoading && intent.trim() ? { scale: 0.98 } : {}}
            type="submit"
            disabled={!intent.trim() || isLoading}
            className="btn btn-primary py-3.5 px-6 whitespace-nowrap"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>{isLoading ? 'Executing...' : 'Execute'}</span>
          </motion.button>
        </div>
      </form>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6">
        {[
          { icon: Terminal, label: 'Planner Agent', desc: 'Task decomposition' },
          { icon: Globe, label: 'Knowledge Agent', desc: 'Hybrid RAG search' },
          { icon: Cpu, label: 'Monitoring Agent', desc: 'Real-time metrics' },
          { icon: Activity, label: 'Report Generator', desc: 'Executive reports' },
        ].map(({ icon: Icon, label, desc }) => (
          <div
            key={label}
            className="rounded-xl p-3 text-center bg-[rgba(15,23,42,0.5)] border border-[rgba(255,255,255,0.04)]
                       hover:border-[rgba(99,102,241,0.12)] transition-all duration-200"
          >
            <div className="w-8 h-8 rounded-lg bg-[rgba(99,102,241,0.1)] flex items-center justify-center mx-auto mb-2">
              <Icon className="w-4 h-4 text-[#818cf8]" />
            </div>
            <h4 className="text-xs font-semibold text-[#e2e8f0]">{label}</h4>
            <p className="text-[10px] text-[#64748b] mt-0.5">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NetworkInput;
