import { motion } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import {
  Activity, Shield, Clock, CheckCircle, AlertTriangle, Server,
  Database, Terminal, Users, Cpu, BarChart3, Sparkles
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { networkAPI } from '../services/api';

const PALETTE = {
  primary: '#D97757',
  success: '#3F9142',
  warning: '#B06000',
  danger: '#C5523F',
};

const MetricCard = ({ icon: Icon, label, value, sub, color = 'primary' }) => (
  <div className="rounded-xl p-3 bg-paper/70 border border-paper-line">
    <div className="flex items-center gap-2 mb-1.5">
      <Icon className="w-3.5 h-3.5" style={{ color: PALETTE[color] }} />
      <span className="text-[10px] font-medium text-ink-mute">{label}</span>
    </div>
    <div className="text-lg font-bold" style={{ color: PALETTE[color] }}>{value}</div>
    {sub && <div className="text-[10px] text-ink-faint mt-0.5">{sub}</div>}
  </div>
);

const Section = ({ icon: Icon, title, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-2xl bg-paper/60 border border-paper-line overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-3 hover:bg-paper-hover transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-clay" />
          <span className="text-sm font-medium text-ink">{title}</span>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="w-4 h-4 text-ink-mute" />
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
          <MetricCard icon={Sparkles} label="Agents" value="12" color="primary" />
          <MetricCard icon={Terminal} label="Tools" value={String(tools.length)} color="success" />
          <MetricCard icon={Shield} label="Audit Actions" value={auditStats?.total_actions || '0'} color="warning" />
          <MetricCard icon={Activity} label="Eval Calls" value={evalStats?.total_actions || '0'} color="primary" />
        </div>
      </Section>

      <Section icon={Terminal} title={`Tools (${tools.length})`}>
        {tools.length === 0 ? (
          <p className={`text-xs ${'text-ink-mute'}`}>Loading...</p>
        ) : (
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {tools.map(t => (
              <div key={t.name} className={`flex items-center gap-2 text-xs ${'text-ink-soft'} py-1`}>
                <CheckCircle className="w-3 h-3 text-[#3F9142] flex-shrink-0" />
                <span className="truncate">{t.name}</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section icon={Database} title="Memory & Context">
        <div className="space-y-2.5 text-xs text-ink-soft">
          <div className="flex items-center gap-2.5">
            <Clock className="w-3.5 h-3.5 text-ink-mute" />
            <span>Session: {workflowId ? <span className="text-[#3F9142] font-medium">Active</span> : 'None'}</span>
          </div>
          <div className="flex items-center gap-2.5">
            <Users className="w-3.5 h-3.5 text-ink-mute" />
            <span>RBAC: Admin / Engineer / Viewer</span>
          </div>
          <div className="flex items-center gap-2.5">
            <Shield className="w-3.5 h-3.5 text-ink-mute" />
            <span>Guardrails: <span className="text-[#3F9142] font-medium">Active</span></span>
          </div>
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-3.5 h-3.5 text-ink-mute" />
            <span>Approval: Required for config changes</span>
          </div>
        </div>
      </Section>

      <Section icon={Cpu} title="Model Registry">
        <p className="text-xs text-ink-soft leading-relaxed">
          Bring your own OpenAI, Anthropic, or Groq key. Switch models anytime from the composer.
        </p>
      </Section>

      {evalStats && (
        <Section icon={Activity} title="Evaluation Metrics">
          <div className="space-y-2 text-xs">
            <div className={`flex justify-between ${'text-ink-soft'}`}>
              <span>Avg Latency</span>
              <span className="font-medium text-ink">{Math.round(evalStats.avg_latency_ms || 0)}ms</span>
            </div>
            <div className={`flex justify-between ${'text-ink-soft'}`}>
              <span>Success Rate</span>
              <span className="font-medium text-[#3F9142]">
                {evalStats.total_actions > 0
                  ? Math.round((evalStats.successful_actions / evalStats.total_actions) * 100)
                  : 0}%
              </span>
            </div>
            <div className={`flex justify-between ${'text-ink-soft'}`}>
              <span>Total Tokens</span>
              <span className="font-medium text-ink">{(evalStats.total_tokens || 0).toLocaleString()}</span>
            </div>
          </div>
        </Section>
      )}

      {auditStats && (
        <Section icon={Shield} title="Audit Activity">
          <div className="space-y-1.5 text-xs max-h-32 overflow-y-auto">
            {Object.entries(auditStats.action_breakdown || {}).slice(0, 6).map(([action, count]) => (
              <div key={action} className={`flex justify-between items-center ${'text-ink-soft'}`}>
                <span className="truncate mr-2">{action}</span>
                <span className="font-medium text-ink flex-shrink-0">{count}</span>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
};

export default EnterprisePanel;