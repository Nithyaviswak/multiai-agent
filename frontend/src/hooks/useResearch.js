import { useState, useCallback } from 'react';
import { networkAPI } from '../services/api';
import toast from 'react-hot-toast';

export const useNetworkAutomation = () => {
  const [state, setState] = useState({
    isLoading: false,
    data: null,
    error: null,
    workflowId: null,
    currentStep: null,
  });

  const startWorkflow = useCallback(async (intent, environment = 'devnet-sandbox', sessionId = 'default', userId = 'engineer') => {
    setState({ isLoading: true, data: null, error: null, workflowId: null, currentStep: 'plan' });

    try {
      const response = await networkAPI.startNetworkWorkflow(intent, environment, sessionId, userId);

      if (response.success) {
        setState(prev => ({ ...prev, workflowId: response.workflow_id }));
        const result = await networkAPI.pollWorkflowStatus(response.workflow_id);

        setState({
          isLoading: false,
          data: result.data ? { ...result.data, workflow_id: response.workflow_id } : null,
          error: result.error,
          workflowId: response.workflow_id,
          currentStep: result.data?.current_step || (result.error ? 'error' : 'complete'),
        });

        if (result.error) toast.error('Workflow failed: ' + result.error);
        else toast.success('Network automation completed!');
      } else {
        throw new Error(response.error || 'Failed to start workflow');
      }
    } catch (error) {
      setState({ isLoading: false, data: null, error: error.message, workflowId: null, currentStep: 'error' });
      toast.error('Workflow failed: ' + error.message);
    }
  }, []);

  const approveAction = useCallback(async (workflowId, approved, userId = 'engineer') => {
    try {
      const response = await networkAPI.approveAction(workflowId, approved, userId);
      if (response.success) {
        toast.success(approved ? 'Action approved' : 'Action denied');
        // Refetch workflow state
        const result = await networkAPI.getWorkflowStatus(workflowId);
        setState(prev => ({ ...prev, data: result.data }));
      }
    } catch (error) {
      toast.error('Approval failed: ' + error.message);
    }
  }, []);

  const resetWorkflow = useCallback(() => {
    setState({ isLoading: false, data: null, error: null, workflowId: null, currentStep: null });
  }, []);

  return { state, startWorkflow, approveAction, resetWorkflow };
};
