import { useState, useCallback } from 'react';
import { researchAPI } from '../services/api';
import toast from 'react-hot-toast';

export const useResearch = () => {
  const [researchState, setResearchState] = useState({
    isLoading: false,
    data: null,
    error: null,
    workflowId: null,
    currentStep: null,
  });

  const startResearch = useCallback(async (topic) => {
    setResearchState({
      isLoading: true,
      data: null,
      error: null,
      workflowId: null,
      currentStep: 'research',
    });

    try {
      const response = await researchAPI.startResearch(topic);
      
      if (response.success) {
        setResearchState(prev => ({
          ...prev,
          workflowId: response.workflow_id,
        }));

        // Start polling for results
        const result = await researchAPI.pollResearchStatus(response.workflow_id);
        const dataWithWorkflowId = result.data
          ? { ...result.data, workflow_id: response.workflow_id }
          : null;
        
        setResearchState({
          isLoading: false,
          data: dataWithWorkflowId,
          error: result.error,
          workflowId: response.workflow_id,
          currentStep: result.data?.current_step || (result.error ? 'error' : 'complete'),
        });

        if (result.error) {
          toast.error('Research failed: ' + result.error);
        } else {
          toast.success('Research completed successfully!');
        }
      } else {
        throw new Error(response.error || 'Failed to start research');
      }
    } catch (error) {
      console.error('Research error:', error);
      setResearchState({
        isLoading: false,
        data: null,
        error: error.message,
        workflowId: null,
        currentStep: 'error',
      });
      toast.error('Research failed: ' + error.message);
    }
  }, []);

  const resetResearch = useCallback(() => {
    setResearchState({
      isLoading: false,
      data: null,
      error: null,
      workflowId: null,
      currentStep: null,
    });
  }, []);

  return {
    researchState,
    startResearch,
    resetResearch,
  };
};
