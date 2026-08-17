import { motion } from 'framer-motion';
import {
  CheckCircle, XCircle, AlertTriangle, Server, Terminal, Shield,
  Activity, FileText, Zap, ArrowRight, Globe, Cpu, Network,
  BarChart3, AlertCircle, ChevronDown
} from 'lucide-react';
import { useState } from 'react';

const PALETTE = {
  primary: '#D97757',
  success: '#3F9142',
  warning: '#B06000',
  danger: '#C5523F',
  cyan: '#C15F3F',
  purple: '#A34E33',
};

const CollapsibleSection = ({ title, icon: Icon, color = 'primary', defaultOpen = true, children }) => {
  const [open, setOpen] = useState(defaultOpen);
  const dotColor = PALETTE[color] || PALETTE.primary;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card overflow-hidden"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 hover:bg-paper-hover transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: `${dotColor}18` }}>
            <Icon className="w-4 h-4" style={{ color: dotColor }} />
          </div>
          <span className="text-sm font-semibold text-ink">{title}</span>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="w-4 h-4 text-ink-mute" />
        </motion.div>
      </button>
      <motion.div
        initial={false}
        animate={{ height: open ? 'auto' : 0, opacity: open ? 1 : 0 }}
        transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
        className="overflow-hidden"
      >
        <div className="px-4 pb-4 space-y-3">{children}</div>
      </motion.div>
    </motion.div>
  );
};

const Badge = ({ variant = 'default', children }) => {
  const variants = {
    default: 'bg-clay-soft text-clay-deep border-[rgba(217,119,87,0.18)]',
    success: 'bg-[rgba(63,145,66,0.10)] text-[#3F9142] border-[rgba(63,145,66,0.18)]',
    warning: 'bg-[rgba(176,96,0,0.10)] text-[#B06000] border-[rgba(176,96,0,0.18)]',
    danger: 'bg-[rgba(197,82,63,0.10)] text-[#C5523F] border-[rgba(197,82,63,0.18)]',
    info: 'bg-paper-inset text-ink-soft border-transparent',
  };
  const cls = variants[variant] || variants.default;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-medium border ${cls}`}>
      {children}
    </span>
  );
};

const StatCard = ({ label, value, icon: Icon, color = 'primary' }) => {
  return (
    <div className="rounded-xl p-3.5 bg-paper/70 border border-paper-line">
      <div className="flex items-center gap-2 mb-1.5">
        <Icon className="w-3.5 h-3.5" style={{ color: PALETTE[color] }} />
        <span className="text-[10px] font-medium text-ink-mute uppercase tracking-wider">{label}</span>
      </div>
      <span className="text-lg font-bold" style={{ color: PALETTE[color] }}>{value}</span>
    </div>
  );
};

const NetworkResults = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="card p-5">
            <div className="skeleton h-5 w-1/3 mb-3" />
            <div className="skeleton h-3 w-full mb-2" />
            <div className="skeleton h-3 w-2/3" />
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
  const sub = 'text-xs';
  const subMute = 'text-ink-mute';
  const hard = 'text-ink';
  const chip = 'rounded-xl p-3 bg-paper/70 border border-paper-line';

  if (summary_data) {
    sections.push(
      <CollapsibleSection key="summary" title="Executive Summary" icon={FileText} color="primary">
        <div className="grid grid-cols-2 gap-2">
          <StatCard label="Devices" value={topology_data?.device_count || 0} icon={Server} color="primary" />
          <StatCard label="Configured" value={config_data?.total_devices || 0} icon={Zap} color="success" />
          <StatCard label="Compliance" value={`${compliance_data?.overall_score || 0}%`} icon={Shield} color="warning" />
          <StatCard label="Health" value={`${log_analysis_data?.average_health_score || 0}%`} icon={Activity} color="primary" />
        </div>
        <div className="flex items-center gap-3 pt-1">
          <Badge variant={summary_data.workflow_status === 'completed' ? 'success' : 'warning'}>
            {summary_data.workflow_status || 'completed'}
          </Badge>
          <span className={`${sub} ${subMute}`}>{summary_data.title || intent_data?.intent_summary}</span>
        </div>
        {summary_data.sections && Object.keys(summary_data.sections).length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {Object.keys(summary_data.sections).slice(0, 5).map(s => (
              <span key={s} className="text-[10px] px-2 py-0.5 rounded bg-paper-inset text-ink-mute">{s}</span>
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
              <div key={label} className={`flex justify-between items-center ${subMute}`}>
                <span>{label}</span>
                <span className={`font-medium ${hard}`}>{value}</span>
              </div>
            ))}
          </div>
          <div>
            <span className="text-[10px] font-medium text-ink-mute uppercase tracking-wider">Target Devices</span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {(intent_data.target_devices || []).map(d => (
                <span key={d} className="px-2.5 py-0.5 rounded-full bg-clay-soft text-clay-deep text-[10px] font-medium">{d}</span>
              ))}
            </div>
          </div>
        </div>
        {intent_data.parameters?.tasks?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-paper-line">
            <span className="text-[10px] font-medium text-ink-mute uppercase tracking-wider">Planned Tasks</span>
            <div className="space-y-1.5 mt-1.5">
              {intent_data.parameters.tasks.map((t, i) => (
                <div key={i} className={`flex items-start gap-2 ${sub} ${subMute}`}>
                  <CheckCircle className="w-3 h-3 text-[#3F9142] mt-0.5 flex-shrink-0" />
                  <span>{t.description || t.action} on <span className="text-clay-deep font-medium">{t.target}</span></span>
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
            <span className="text-[10px] font-medium text-ink-mute uppercase tracking-wider">Internal KB</span>
            <div className="space-y-1.5 mt-1.5">
              {knowledge_data.internal_knowledge.slice(0, 3).map((k, i) => (
                <div key={i} className={`${sub} ${subMute} ${chip}`}>
                  <span className="text-clay-deep font-medium">{k.keyword}: </span>
                  {k.content?.slice(0, 120)}...
                </div>
              ))}
            </div>
          </div>
        )}
        {knowledge_data.web_sources?.length > 0 && (
          <div className="mt-2">
            <span className="text-[10px] font-medium text-ink-mute uppercase tracking-wider">Web Sources</span>
            <div className="space-y-1 mt-1">
              {knowledge_data.web_sources.slice(0, 3).map((s, i) => (
                <div key={i} className={`${sub} ${subMute}`}>{s.title?.slice(0, 80)}</div>
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
        {topology_data.health_summary && <p className={sub + ' ' + subMute}>{topology_data.health_summary}</p>}
        {topology_data.devices?.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            {topology_data.devices.map(d => (
              <div key={d.hostname} className={`flex items-center gap-2 ${chip}`}>
                <Server className="w-3.5 h-3.5 text-[#3F9142] flex-shrink-0" />
                <div className="min-w-0">
                  <span className={`${sub} font-medium ${hard}`}>{d.hostname}</span>
                  <span className={`text-[10px] ${subMute} ml-1.5`}>({d.role})</span>
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
        <div className="grid grid-cols-2 gap-2">
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
            <span className="text-[10px] font-medium text-ink-mute uppercase tracking-wider">Active Alerts</span>
            {monitoring_data.alerts.slice(0, 3).map((a, i) => (
              <div key={i} className={`flex items-center gap-2 ${sub} bg-[rgba(197,82,63,0.07)] rounded-lg p-2 text-[#C5523F]`}>
                <AlertCircle className="w-3 h-3 flex-shrink-0" />
                <span>{a.message}</span>
              </div>
            ))}
          </div>
        )}
        {monitoring_data.metrics && Object.keys(monitoring_data.metrics).length > 0 && (
          <div className="grid grid-cols-2 gap-2 pt-1">
            {Object.entries(monitoring_data.metrics).slice(0, 4).map(([dev, m]) => (
              <div key={dev} className={`${sub} ${chip}`}>
                <span className={`font-medium ${hard}`}>{dev}</span>
                <div className={`flex justify-between ${subMute} mt-1`}><span>CPU</span><span>{m.cpu}%</span></div>
                <div className={`flex justify-between ${subMute}`}><span>Mem</span><span>{m.memory}%</span></div>
                <div className={`flex justify-between ${subMute}`}><span>Latency</span><span>{m.latency_ms}ms</span></div>
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
          <span className={sub + ' ' + subMute}>Technology: {config_data.technology}</span>
        </div>
        {config_data.configurations?.map(cfg => (
          <div key={cfg.hostname} className={chip}>
            <div className="flex items-center justify-between mb-2">
              <span className={`${sub} font-medium ${hard} flex items-center gap-1.5`}>
                <Terminal className="w-3.5 h-3.5 text-clay" /> {cfg.hostname}
              </span>
              <span className={`text-[10px] ${subMute}`}>{cfg.config_lines?.length || 0} lines</span>
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
              <div key={i} className={`flex items-center gap-2 ${sub} ${subMute}`}>
                {r.status === 'success' ? <CheckCircle className="w-3 h-3 text-[#3F9142]" /> :
                 r.status === 'blocked' ? <XCircle className="w-3 h-3 text-[#C5523F]" /> :
                 <AlertCircle className="w-3 h-3 text-[#B06000]" />}
                <span>{r.action} on <span className="text-clay-deep font-medium">{r.device}</span>: {r.status}</span>
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
          <div key={v.device} className={chip}>
            <div className="flex items-center justify-between mb-2">
              <span className={`${sub} font-medium ${hard}`}>{v.device}</span>
              <Badge variant={v.overall_status === 'pass' ? 'success' : 'danger'}>{v.overall_status}</Badge>
            </div>
            {v.verification_checks?.map((c, i) => (
              <div key={i} className={`flex items-center justify-between ${sub} text-ink-soft py-1`}>
                <span className="flex items-center gap-1.5">
                  {c.status ? <CheckCircle className="w-3 h-3 text-[#3F9142]" /> : <XCircle className="w-3 h-3 text-[#C5523F]" />}
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
        <div className="grid grid-cols-2 gap-2">
          <StatCard label="Passed" value={compliance_data.passed} icon={CheckCircle} color="success" />
          <StatCard label="Failed" value={compliance_data.failed} icon={XCircle} color="danger" />
          <StatCard label="Warnings" value={compliance_data.warnings} icon={AlertTriangle} color="warning" />
          <StatCard label="Score" value={`${compliance_data.overall_score}%`} icon={BarChart3} color="primary" />
        </div>
        <div className="w-full h-1.5 rounded-full bg-paper-inset overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${compliance_data.overall_score}%` }}
            transition={{ duration: 1, ease: [0.4, 0, 0.2, 1] }}
            className={`h-full rounded-full ${
              compliance_data.overall_score >= 70 ? 'bg-[#3F9142]' :
              compliance_data.overall_score >= 40 ? 'bg-[#B06000]' : 'bg-[#C5523F]'
            }`}
          />
        </div>
        {compliance_data.remediation_plan?.length > 0 && (
          <div className="rounded-xl p-3 bg-[rgba(176,96,0,0.06)] border border-[rgba(176,96,0,0.14)]">
            <span className={`${sub} font-medium text-[#B06000] flex items-center gap-1.5`}>
              <AlertTriangle className="w-3 h-3" /> Remediation Plan
            </span>
            <ul className="mt-2 space-y-1">
              {compliance_data.remediation_plan.map((r, i) => (
                <li key={i} className={`flex items-start gap-1.5 ${sub} ${subMute}`}>
                  <ArrowRight className="w-3 h-3 text-[#B06000] mt-0.5 flex-shrink-0" />
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
        <div className="grid grid-cols-1 gap-3">
          <div className={`space-y-1.5 ${sub}`}>
            <div className={`flex justify-between ${subMute}`}>
              <span>ID</span>
              <span className={`font-medium ${hard}`}>{incident_response_data.incident_id}</span>
            </div>
            <div className={`flex items-center gap-2 ${subMute}`}>
              <span>Severity</span>
              <Badge variant={incident_response_data.severity === 'critical' ? 'danger' : 'warning'}>
                {incident_response_data.severity}
              </Badge>
            </div>
          </div>
          <div className={`space-y-1 ${sub} ${subMute}`}>
            <p><span className="text-ink-mute">Root Cause: </span>{incident_response_data.root_cause}</p>
            <p><span className="text-ink-mute">Impact: </span>{incident_response_data.impact_analysis}</p>
          </div>
        </div>
      </CollapsibleSection>
    );
  }

  if (sections.length === 0) return null;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      {sections}
    </motion.div>
  );
};

export default NetworkResults;