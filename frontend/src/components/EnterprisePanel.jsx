import { motion } from 'framer-motion';
import {
  Activity, Shield, Clock, CheckCircle, AlertTriangle, Server,
  Database, Terminal, Users, Cpu, BarChart3, Globe, Zap, Network
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { networkAPI } from '../services/api';

const MetricCard = ({ icon: Icon, label, value, sub, color = 'primary' }) => {
  const colors = {
    primary: 'from-[#6366f1] to-[#06b6d4]',
    success: 'from-[#10b981] to-[#34d399]',
    warning: 'from-[#f59e0b] to-[#fbbf24]',
    danger: 'from-[#ef4444] to-[#f87171]',
  };

  return (
    <div className="rounded-xl p-3.5 bg-[rgba(15,23,42,0.5)] border border-[rgba(255,255,255,0.04)]">
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-8 h-8 rounded-lg bg-[rgba(99,102,241,0.1)] flex items-center justify-center`}>
          <Icon className="w-4 h-4 text-[#818cf8]" />
        </div>
        <span className="text-xs font-medium text-[#94a3b8]">{label}</span>
      </div>
      <div className={`text-xl font-bold bg-gradient-to-r ${colors[color]} bg-clip-text text-transparent`}>
        {value}
      </div>
      {sub && <div className="text-[10px] text-[#64748b] mt-0.5">{sub}</div>}
    </div>
  );
};

const Section = ({ icon: Icon, title, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl bg-[rgba(15,23,42,0.4)] border border-[rgba(255,255,255,0.04)] overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-3.5 hover:bg-[rgba(99,102,241,0.04)] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-[#818cf8]" />
          <span className="text-sm font-medium text-[#e2e8f0]">{title}</span>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="w-4 h-4 text-[#64748b]" />
        </motion.div>
      </button>
      <motion.div
        initial={false}
        animate={{ height: open ? 'auto' : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.2 }}
        className="overflow-hidden"
      >
        <div className="px-3.5 pb-3.5">{children}</div>
      </motion.div>
    </div>
  );
};

import { ChevronDown } from 'lucide-react';

const EnterprisePanel = ({ workflowId }) => {
  const [tools, setTools] = useState([]);
  const [auditStats, setAuditStats] = useState(null);
  const [evalStats, setEvalStats] = useState(null);

  useEffect(() => {
    networkAPI.listTools().then(r => r.success && setTools(r.tools)).catch(() => {});
    networkAPI.getAuditStats().then(r => r.success && setAuditStats(r.stats)).catch(() => {});
    networkAPI.getEvalStats().then(r => r.success && setEvalStats(r.stats)).catch(() => {});
  }, [workflowId]);

  return (
    <div className="space-y-3">
      <Section icon={BarChart3} title="Platform Metrics">
        <div className="grid grid-cols-2 gap-2">
          <MetricCard icon={Server} label="Agents" value="12" color="primary" />
          <MetricCard icon={Terminal} label="Tools" value={String(tools.length)} color="success" />
          <MetricCard icon={Shield} label="Audit Actions" value={auditStats?.total_actions || '0'} color="warning" />
          <MetricCard icon={Activity} label="Eval Calls" value={evalStats?.total_actions || '0'} color="primary" />
        </div>
      </Section>

      <Section icon={Terminal} title={`Tools (${tools.length})`}>
        {tools.length === 0 ? (
          <p className="text-xs text-[#64748b]">Loading...</p>
        ) : (
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {tools.map(t => (
              <div key={t.name} className="flex items-center gap-2 text-xs text-[#94a3b8] py-1">
                <CheckCircle className="w-3 h-3 text-[#34d399] flex-shrink-0" />
                <span className="truncate">{t.name}</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section icon={Database} title="Memory & Context">
        <div className="space-y-2.5 text-xs">
          <div className="flex items-center gap-2.5 text-[#94a3b8]">
            <Clock className="w-3.5 h-3.5 text-[#64748b]" />
            <span>Session: {workflowId ? <span className="text-[#34d399]">Active</span> : 'None'}</span>
          </div>
          <div className="flex items-center gap-2.5 text-[#94a3b8]">
            <Users className="w-3.5 h-3.5 text-[#64748b]" />
            <span>RBAC: Admin / Engineer / Viewer</span>
          </div>
          <div className="flex items-center gap-2.5 text-[#94a3b8]">
            <Shield className="w-3.5 h-3.5 text-[#64748b]" />
            <span>Guardrails: <span className="text-[#34d399]">Active</span></span>
          </div>
          <div className="flex items-center gap-2.5 text-[#94a3b8]">
            <AlertTriangle className="w-3.5 h-3.5 text-[#64748b]" />
            <span>Approval: Required for config changes</span>
          </div>
        </div>
      </Section>

      {evalStats && (
        <Section icon={Activity} title="Evaluation Metrics">
          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-[#94a3b8]">
              <span>Avg Latency</span>
              <span className="font-medium text-[#e2e8f0]">{Math.round(evalStats.avg_latency_ms || 0)}ms</span>
            </div>
            <div className="flex justify-between text-[#94a3b8]">
              <span>Success Rate</span>
              <span className="font-medium text-[#34d399]">
                {evalStats.total_actions > 0
                  ? Math.round((evalStats.successful_actions / evalStats.total_actions) * 100)
                  : 0}%
              </span>
            </div>
            <div className="flex justify-between text-[#94a3b8]">
              <span>Total Tokens</span>
              <span className="font-medium text-[#e2e8f0]">{(evalStats.total_tokens || 0).toLocaleString()}</span>
            </div>
          </div>
        </Section>
      )}

      {auditStats && (
        <Section icon={Shield} title="Audit Activity">
          <div className="space-y-1.5 text-xs max-h-28 overflow-y-auto">
            {Object.entries(auditStats.action_breakdown || {}).slice(0, 6).map(([action, count]) => (
              <div key={action} className="flex justify-between items-center text-[#94a3b8]">
                <span className="truncate mr-2">{action}</span>
                <span className="font-medium text-[#e2e8f0] flex-shrink-0">{count}</span>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
};

export default EnterprisePanel;
