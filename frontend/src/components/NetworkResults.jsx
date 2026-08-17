import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle, XCircle, AlertTriangle, Server, Terminal, Shield,
  Activity, FileText, Zap, ArrowRight, Globe, Cpu, BookOpen, Network,
  BarChart3, Clock, AlertCircle, ChevronDown
} from 'lucide-react';
import { useState } from 'react';

const CollapsibleSection = ({ title, icon: Icon, color = 'primary', defaultOpen = true, children }) => {
  const [open, setOpen] = useState(defaultOpen);
  const colors = { primary: '#6366f1', success: '#10b981', warning: '#f59e0b', danger: '#ef4444', cyan: '#06b6d4', purple: '#8b5cf6' };
  const dotColor = colors[color] || '#6366f1';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card overflow-hidden"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 sm:p-5 hover:bg-[rgba(99,102,241,0.03)] transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: `${dotColor}15` }}>
            <Icon className="w-4 h-4" style={{ color: dotColor }} />
          </div>
          <span className="text-sm font-semibold text-[#e2e8f0]">{title}</span>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="w-4 h-4 text-[#64748b]" />
        </motion.div>
      </button>
      <motion.div
        initial={false}
        animate={{ height: open ? 'auto' : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
        className="overflow-hidden"
      >
        <div className="px-4 sm:px-5 pb-4 sm:pb-5 space-y-3">
          {children}
        </div>
      </motion.div>
    </motion.div>
  );
};

const Badge = ({ variant = 'default', children }) => {
  const variants = {
    default: 'bg-[rgba(99,102,241,0.1)] text-[#818cf8] border-[rgba(99,102,241,0.15)]',
    success: 'bg-[rgba(16,185,129,0.1)] text-[#34d399] border-[rgba(16,185,129,0.15)]',
    warning: 'bg-[rgba(245,158,11,0.1)] text-[#fbbf24] border-[rgba(245,158,11,0.15)]',
    danger: 'bg-[rgba(239,68,68,0.1)] text-[#f87171] border-[rgba(239,68,68,0.15)]',
    info: 'bg-[rgba(6,182,212,0.1)] text-[#22d3ee] border-[rgba(6,182,212,0.15)]',
  };
  const cls = variants[variant] || variants.default;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-medium border ${cls}`}>
      {children}
    </span>
  );
};

const StatCard = ({ label, value, icon: Icon, color = 'primary' }) => {
  const colors = { primary: '#6366f1', success: '#10b981', warning: '#f59e0b', danger: '#ef4444' };
  return (
    <div className="rounded-xl p-3.5 bg-[rgba(15,23,42,0.5)] border border-[rgba(255,255,255,0.04)]">
      <div className="flex items-center gap-2 mb-1.5">
        <Icon className="w-3.5 h-3.5" style={{ color: colors[color] }} />
        <span className="text-[10px] font-medium text-[#64748b] uppercase tracking-wider">{label}</span>
      </div>
      <span className="text-lg font-bold" style={{ color: colors[color] }}>{value}</span>
    </div>
  );
};

const NetworkResults = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="card p-5">
            <div className="skeleton h-5 w-1/3 mb-3 rounded" />
            <div className="skeleton h-3 w-full mb-2 rounded" />
            <div className="skeleton h-3 w-2/3 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (!data) return null;

  const {
    intent_data, knowledge_data, topology_data, config_data,
    verification_data, compliance_data, log_analysis_data,
    incident_response_data, monitoring_data, automation_data, summary_data
  } = data;

  const sections = [];

  if (summary_data) {
    sections.push(
      <CollapsibleSection key="summary" title="Executive Summary" icon={FileText} color="primary">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <StatCard label="Devices" value={topology_data?.device_count || 0} icon={Server} color="primary" />
          <StatCard label="Configured" value={config_data?.total_devices || 0} icon={Zap} color="success" />
          <StatCard label="Compliance" value={`${compliance_data?.overall_score || 0}%`} icon={Shield} color="warning" />
          <StatCard label="Health" value={`${log_analysis_data?.average_health_score || 0}%`} icon={Activity} color="primary" />
        </div>
        <div className="flex items-center gap-3 pt-2">
          <Badge variant={summary_data.workflow_status === 'completed' ? 'success' : 'warning'}>
            {summary_data.workflow_status || 'completed'}
          </Badge>
          <span className="text-xs text-[#94a3b8]">{summary_data.title || intent_data?.intent_summary}</span>
        </div>
        {summary_data.sections && Object.keys(summary_data.sections).length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-2">
            {Object.keys(summary_data.sections).slice(0, 5).map(s => (
              <span key={s} className="text-[10px] px-2 py-0.5 rounded bg-[rgba(99,102,241,0.06)] text-[#64748b]">{s}</span>
            ))}
          </div>
        )}
      </CollapsibleSection>
    );
  }

  if (intent_data) {
    sections.push(
      <CollapsibleSection key="intent" title="Plan & Intent" icon={Terminal} color="primary">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5 text-xs">
            {[
              ['Action', intent_data.action],
              ['Technology', intent_data.technology],
              ['Priority', <Badge key="p" variant={intent_data.priority === 'high' ? 'danger' : 'warning'}>{intent_data.priority}</Badge>],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between items-center text-[#94a3b8]">
                <span>{label}</span>
                <span className="font-medium text-[#e2e8f0]">{value}</span>
              </div>
            ))}
          </div>
          <div>
            <span className="text-[10px] font-medium text-[#64748b] uppercase tracking-wider">Target Devices</span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {(intent_data.target_devices || []).map(d => (
                <span key={d} className="badge badge-primary text-[10px]">{d}</span>
              ))}
            </div>
          </div>
        </div>
        {intent_data.parameters?.tasks?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-[rgba(255,255,255,0.04)]">
            <span className="text-[10px] font-medium text-[#64748b] uppercase tracking-wider">Planned Tasks</span>
            <div className="space-y-1.5 mt-1.5">
              {intent_data.parameters.tasks.map((t, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-[#94a3b8]">
                  <CheckCircle className="w-3 h-3 text-[#34d399] mt-0.5 flex-shrink-0" />
                  <span>{t.description || t.action} on <span className="text-[#818cf8]">{t.target}</span></span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CollapsibleSection>
    );
  }

  if (knowledge_data) {
    sections.push(
      <CollapsibleSection key="knowledge" title="Knowledge Retrieval" icon={Globe} color="cyan">
        <Badge variant="info">{knowledge_data.total_sources || 0} sources</Badge>
        {knowledge_data.internal_knowledge?.length > 0 && (
          <div className="mt-3">
            <span className="text-[10px] font-medium text-[#64748b] uppercase tracking-wider">Internal KB</span>
            <div className="space-y-1.5 mt-1.5">
              {knowledge_data.internal_knowledge.slice(0, 3).map((k, i) => (
                <div key={i} className="text-xs text-[#94a3b8] p-2 rounded-lg bg-[rgba(15,23,42,0.5)]">
                  <span className="text-[#818cf8]">{k.keyword}: </span>
                  {k.content?.slice(0, 120)}...
                </div>
              ))}
            </div>
          </div>
        )}
        {knowledge_data.web_sources?.length > 0 && (
          <div className="mt-2">
            <span className="text-[10px] font-medium text-[#64748b] uppercase tracking-wider">Web Sources</span>
            <div className="space-y-1 mt-1">
              {knowledge_data.web_sources.slice(0, 3).map((s, i) => (
                <div key={i} className="text-xs text-[#64748b]">{s.title?.slice(0, 80)}</div>
              ))}
            </div>
          </div>
        )}
      </CollapsibleSection>
    );
  }

  if (topology_data) {
    sections.push(
      <CollapsibleSection key="topology" title="Network Topology" icon={Server} color="success">
        <div className="grid grid-cols-2 gap-3">
          <StatCard label="Environment" value={topology_data.environment || 'N/A'} icon={Server} color="primary" />
          <StatCard label="Devices" value={topology_data.device_count || 0} icon={Network} color="success" />
        </div>
        {topology_data.health_summary && (
          <p className="text-xs text-[#94a3b8]">{topology_data.health_summary}</p>
        )}
        {topology_data.devices?.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            {topology_data.devices.map(d => (
              <div key={d.hostname} className="flex items-center gap-2 rounded-lg p-2 bg-[rgba(15,23,42,0.5)] border border-[rgba(255,255,255,0.04)]">
                <Server className="w-3.5 h-3.5 text-[#34d399] flex-shrink-0" />
                <div className="min-w-0">
                  <span className="text-xs font-medium text-[#e2e8f0]">{d.hostname}</span>
                  <span className="text-[10px] text-[#64748b] ml-1.5">({d.role})</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CollapsibleSection>
    );
  }

  if (monitoring_data) {
    sections.push(
      <CollapsibleSection key="monitoring" title="Monitoring Metrics" icon={Activity} color="warning">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <StatCard label="Devices" value={monitoring_data.total_devices} icon={Server} color="primary" />
          <StatCard label="Alerts" value={monitoring_data.active_alerts} icon={AlertTriangle} color="danger" />
          <div className="col-span-2 flex items-center">
            <Badge variant={monitoring_data.overall_health === 'healthy' ? 'success' : monitoring_data.overall_health === 'degraded' ? 'warning' : 'danger'}>
              {monitoring_data.overall_health}
            </Badge>
          </div>
        </div>
        {monitoring_data.alerts?.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] font-medium text-[#64748b] uppercase tracking-wider">Active Alerts</span>
            {monitoring_data.alerts.slice(0, 3).map((a, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-[#f87171] bg-[rgba(239,68,68,0.06)] rounded-lg p-2">
                <AlertCircle className="w-3 h-3 flex-shrink-0" />
                <span>{a.message}</span>
              </div>
            ))}
          </div>
        )}
        {monitoring_data.metrics && Object.keys(monitoring_data.metrics).length > 0 && (
          <div className="grid grid-cols-2 gap-2 pt-1">
            {Object.entries(monitoring_data.metrics).slice(0, 4).map(([dev, m]) => (
              <div key={dev} className="text-xs p-2 rounded-lg bg-[rgba(15,23,42,0.5)] border border-[rgba(255,255,255,0.04)]">
                <span className="text-[#e2e8f0] font-medium">{dev}</span>
                <div className="flex justify-between text-[#94a3b8] mt-1"><span>CPU</span><span>{m.cpu}%</span></div>
                <div className="flex justify-between text-[#94a3b8]"><span>Mem</span><span>{m.memory}%</span></div>
                <div className="flex justify-between text-[#94a3b8]"><span>Latency</span><span>{m.latency_ms}ms</span></div>
              </div>
            ))}
          </div>
        )}
      </CollapsibleSection>
    );
  }

  if (config_data) {
    sections.push(
      <CollapsibleSection key="config" title="Configuration Generated" icon={Zap} color="purple">
        <div className="flex items-center gap-3">
          <Badge variant={config_data.generation_status === 'success' ? 'success' : 'warning'}>{config_data.generation_status}</Badge>
          <span className="text-xs text-[#94a3b8]">Technology: {config_data.technology}</span>
        </div>
        {config_data.configurations?.map(cfg => (
          <div key={cfg.hostname} className="rounded-xl p-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(255,255,255,0.04)]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-[#e2e8f0] flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5 text-[#818cf8]" />
                {cfg.hostname}
              </span>
              <span className="text-[10px] text-[#64748b]">{cfg.config_lines?.length || 0} lines</span>
            </div>
            <pre className="code-block text-[10px] max-h-28">{cfg.config_text}</pre>
          </div>
        ))}
      </CollapsibleSection>
    );
  }

  if (automation_data) {
    sections.push(
      <CollapsibleSection key="automation" title="Automation Execution" icon={Cpu} color="cyan">
        <Badge variant={automation_data.all_successful ? 'success' : 'danger'}>
          {automation_data.all_successful ? 'All Successful' : 'Some Failed'}
        </Badge>
        {automation_data.results?.length > 0 && (
          <div className="space-y-1.5 pt-2">
            {automation_data.results.map((r, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-[#94a3b8]">
                {r.status === 'success' ? <CheckCircle className="w-3 h-3 text-[#34d399]" /> :
                 r.status === 'blocked' ? <XCircle className="w-3 h-3 text-[#f87171]" /> :
                 <AlertCircle className="w-3 h-3 text-[#fbbf24]" />}
                <span>{r.action} on <span className="text-[#818cf8]">{r.device}</span>: {r.status}</span>
              </div>
            ))}
          </div>
        )}
      </CollapsibleSection>
    );
  }

  if (verification_data?.verifications?.length > 0) {
    sections.push(
      <CollapsibleSection key="verification" title="Verification" icon={CheckCircle} color="success">
        <Badge variant={verification_data.all_passed ? 'success' : 'danger'}>
          {verification_data.all_passed ? 'All Passed' : 'Some Failed'}
        </Badge>
        {verification_data.verifications.map(v => (
          <div key={v.device} className="rounded-xl p-3 bg-[rgba(15,23,42,0.5)] border border-[rgba(255,255,255,0.04)]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-[#e2e8f0]">{v.device}</span>
              <Badge variant={v.overall_status === 'pass' ? 'success' : 'danger'}>{v.overall_status}</Badge>
            </div>
            {v.verification_checks?.map((c, i) => (
              <div key={i} className="flex items-center justify-between text-xs text-[#94a3b8] py-1">
                <span className="flex items-center gap-1.5">
                  {c.status ? <CheckCircle className="w-3 h-3 text-[#34d399]" /> : <XCircle className="w-3 h-3 text-[#f87171]" />}
                  {c.check}
                </span>
                <span>{c.details}</span>
              </div>
            ))}
          </div>
        ))}
      </CollapsibleSection>
    );
  }

  if (compliance_data) {
    sections.push(
      <CollapsibleSection key="compliance" title="Compliance Audit" icon={Shield} color="danger">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <StatCard label="Passed" value={compliance_data.passed} icon={CheckCircle} color="success" />
          <StatCard label="Failed" value={compliance_data.failed} icon={XCircle} color="danger" />
          <StatCard label="Warnings" value={compliance_data.warnings} icon={AlertTriangle} color="warning" />
          <StatCard label="Score" value={`${compliance_data.overall_score}%`} icon={BarChart3} color="primary" />
        </div>
        <div className="w-full h-1.5 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${compliance_data.overall_score}%` }}
            transition={{ duration: 1, ease: [0.4, 0, 0.2, 1] }}
            className={`h-full rounded-full ${
              compliance_data.overall_score >= 70 ? 'bg-[#10b981]' :
              compliance_data.overall_score >= 40 ? 'bg-[#f59e0b]' : 'bg-[#ef4444]'
            }`}
          />
        </div>
        {compliance_data.remediation_plan?.length > 0 && (
          <div className="rounded-xl p-3 bg-[rgba(245,158,11,0.06)] border border-[rgba(245,158,11,0.12)]">
            <span className="text-xs font-medium text-[#fbbf24] flex items-center gap-1.5">
              <AlertTriangle className="w-3 h-3" /> Remediation Plan
            </span>
            <ul className="mt-2 space-y-1">
              {compliance_data.remediation_plan.map((r, i) => (
                <li key={i} className="flex items-start gap-1.5 text-xs text-[#94a3b8]">
                  <ArrowRight className="w-3 h-3 text-[#fbbf24] mt-0.5 flex-shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CollapsibleSection>
    );
  }

  if (log_analysis_data) {
    sections.push(
      <CollapsibleSection key="logs" title="Log Analysis" icon={Activity} color="warning">
        <div className="grid grid-cols-3 gap-2">
          <StatCard label="Errors" value={log_analysis_data.total_errors} icon={XCircle} color="danger" />
          <StatCard label="Warnings" value={log_analysis_data.total_warnings} icon={AlertTriangle} color="warning" />
          <StatCard label="Health" value={`${log_analysis_data.average_health_score}%`} icon={Activity} color="success" />
        </div>
        <Badge variant={
          log_analysis_data.overall_status === 'healthy' ? 'success' :
          log_analysis_data.overall_status === 'degraded' ? 'warning' : 'danger'
        }>{log_analysis_data.overall_status}</Badge>
      </CollapsibleSection>
    );
  }

  if (incident_response_data?.incident_id) {
    sections.push(
      <CollapsibleSection key="incident" title={`Incident: ${incident_response_data.title || ''}`} icon={AlertCircle} color="danger">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between text-[#94a3b8]">
              <span>ID</span>
              <span className="font-medium text-[#e2e8f0]">{incident_response_data.incident_id}</span>
            </div>
            <div className="flex justify-between text-[#94a3b8]">
              <span>Severity</span>
              <Badge variant={incident_response_data.severity === 'critical' ? 'danger' : 'warning'}>
                {incident_response_data.severity}
              </Badge>
            </div>
          </div>
          <div className="space-y-1 text-xs text-[#94a3b8]">
            <p><span className="text-[#64748b]">Root Cause: </span>{incident_response_data.root_cause}</p>
            <p><span className="text-[#64748b]">Impact: </span>{incident_response_data.impact_analysis}</p>
          </div>
        </div>
      </CollapsibleSection>
    );
  }

  if (sections.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {sections}
    </motion.div>
  );
};

export default NetworkResults;
