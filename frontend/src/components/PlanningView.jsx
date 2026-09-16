import { motion } from 'framer-motion';
import { X, MapPinned } from 'lucide-react';
import AgentTeam from './AgentTeam';
import { AGENTS, stepName } from '../data/agents';

const getProgress = (currentStep) => {
  if (currentStep === 'complete' || currentStep === 'error') return 1;
  const cur = AGENTS.findIndex(a => a.id === currentStep);
  return cur < 0 ? 0 : Math.max(0, cur) / AGENTS.length;
};

const PlanningView = ({ request, currentStep, failedSteps, onStop }) => {
  const progress = getProgress(currentStep);
  const workingName = stepName(currentStep);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: -12 }}
      className="max-w-3xl mx-auto px-4 sm:px-6 py-10 sm:py-16"
    >
      <div className="text-center mb-9">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary-soft text-primary text-[12.5px] font-medium mb-5"
        >
          <span className="relative flex w-2 h-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-60" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
          </span>
          {request?.origin && request?.destination
            ? `${request.origin} → ${request.destination}`
            : 'Planning in progress'}
        </motion.div>

        <h1 className="font-serif text-4xl sm:text-5xl tracking-tight text-balance">
          Building your trip
        </h1>
        <p className="text-[15px] text-ink-soft mt-3">
          Your AI travel team is working together — {workingName} is on it right now.
        </p>
      </div>

      {/* Progress */}
      <div className="mb-8">
        <div className="h-1.5 w-full rounded-full bg-paper-inset overflow-hidden" role="progressbar" aria-valuenow={Math.round(progress * 100)} aria-valuemin={0} aria-valuemax={100}>
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-primary to-secondary"
            animate={{ width: `${Math.round(progress * 100)}%` }}
            transition={{ duration: 0.6, ease: [0.32, 0.72, 0, 1] }}
          />
        </div>
        <div className="flex items-center justify-between mt-2 text-[11px] text-ink-faint">
          <span className="inline-flex items-center gap-1"><MapPinned className="w-3 h-3" /> {Math.round(progress * 100)}% complete</span>
          <span>{AGENTS.length} specialists on the team</span>
        </div>
      </div>

      <AgentTeam currentStep={currentStep} failedSteps={failedSteps} />

      <div className="flex justify-center mt-8">
        <button
          onClick={onStop}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-[12.5px] font-medium text-ink-mute hover:text-ink hover:bg-paper-inset transition-colors"
        >
          <X className="w-3.5 h-3.5" /> Stop planning
        </button>
      </div>
    </motion.div>
  );
};

export default PlanningView;