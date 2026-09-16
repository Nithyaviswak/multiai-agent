import { useState, useCallback, useRef } from 'react';
import { travelAPI } from '../services/api';

const POLL_INTERVAL = 1500;
const POLL_TIMEOUT = 240000;

export const useTravelPlanner = () => {
  const [phase, setPhase] = useState('idle'); // idle | planning | complete | error
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [workflowId, setWorkflowId] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [seenSteps, setSeenSteps] = useState([]);
  const [iterations, setIterations] = useState(0);
  const [lastIntent, setLastIntent] = useState('');
  const active = useRef(false);

  const finish = useCallback((result, flowId, err) => {
    active.current = false;
    setData(result);
    setError(err || null);
    setPhase(err || (result && !result.success) ? 'error' : 'complete');
    setCurrentStep(result?.current_step || 'complete');
  }, []);

  const startWorkflow = useCallback(async (intent, options = {}, opts = {}) => {
    if (active.current) return;
    active.current = true;
    setPhase('planning');
    setData(null);
    setError(null);
    setCurrentStep('plan');
    setSeenSteps(['plan']);
    setLastIntent(intent);
    if (opts.iteration !== undefined) setIterations(opts.iteration);

    try {
      const response = await travelAPI.startTravelWorkflow(intent, options);
      if (!response.success) {
        throw new Error(response.error || 'Failed to start trip planning');
      }
      const flowId = response.workflow_id;
      setWorkflowId(flowId);

      const startAt = Date.now();
      let lastStep = null;
      const loop = async () => {
        if (!active.current) return;
        try {
          const res = await travelAPI.getTravelResult(flowId);
          const step = res.data?.current_step;
          if (step && step !== lastStep) {
            lastStep = step;
            setCurrentStep(step);
            setSeenSteps(prev => (prev.includes(step) ? prev : [...prev, step]));
          }
          const terminal = res.error || res.success === false ||
            step === 'complete' || step === 'error' || res.data?.status?.toLowerCase?.() === 'error';
          if (terminal) {
            finish(res.data || null, flowId, res.error || (step === 'error' ? 'Your trip could not be planned.' : null));
            return;
          }
        } catch (e) {
          if (e?.response?.status === 404) { /* not yet registered — keep polling */ }
          else if (Date.now() - startAt > POLL_TIMEOUT) {
            finish(null, flowId, 'Planning timed out. Try again.');
            return;
          } else {
            // transient network hiccup — keep polling
          }
        }
        if (Date.now() - startAt > POLL_TIMEOUT) {
          finish(null, flowId, 'Planning timed out. Try again.');
          return;
        }
        setTimeout(loop, POLL_INTERVAL);
      };
      setTimeout(loop, POLL_INTERVAL);
    } catch (e) {
      finish(null, null, e.message || 'Failed to start trip planning');
    }
  }, [finish]);

  const refine = useCallback((refinement, options = {}) => {
    const base = lastIntent || 'Plan a trip';
    const next = base.trim().endsWith('.') ? base.trim().slice(0, -1) : base.trim();
    const intent = `${next}. ${refinement.trim().replace(/\.$/, '')}.`;
    startWorkflow(intent, options, { iteration: iterations + 1 });
  }, [lastIntent, iterations, startWorkflow]);

  const resetWorkflow = useCallback(() => {
    active.current = false;
    setPhase('idle');
    setData(null);
    setError(null);
    setWorkflowId(null);
    setCurrentStep(null);
    setSeenSteps([]);
    setIterations(0);
    setLastIntent('');
  }, []);

  return {
    phase, data, error, workflowId, currentStep, seenSteps, iterations,
    startWorkflow, refine, resetWorkflow,
  };
};