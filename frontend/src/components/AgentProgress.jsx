import { motion } from 'framer-motion';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';

const AgentProgress = ({ currentStep, steps, errors }) => {
  const agentSteps = [
    { id: 'research', label: 'Research', description: 'Gathering information from web sources' },
    { id: 'summary', label: 'Summary', description: 'Creating key insights and bullet points' },
    { id: 'report', label: 'Report Writing', description: 'Generating professional report' },
    { id: 'fact_check', label: 'Fact Checking', description: 'Verifying claims and confidence' },
    { id: 'complete', label: 'Complete', description: 'Research workflow finished' },
  ];

  const getStepStatus = (stepId) => {
    if (stepId === currentStep) return 'current';
    const stepIndex = agentSteps.findIndex(s => s.id === stepId);
    const currentIndex = agentSteps.findIndex(s => s.id === currentStep);
    
    if (stepIndex < currentIndex) return 'completed';
    return 'pending';
  };

  const getStepIcon = (status, hasError) => {
    if (hasError) return <AlertCircle className="w-5 h-5 text-red-500" />;
    if (status === 'completed') return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (status === 'current') return <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }}><Clock className="w-5 h-5 text-blue-500" /></motion.div>;
    return <div className="w-5 h-5 rounded-full border-2 border-gray-600" />;
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-dark rounded-2xl p-6 mb-8"
    >
      <h3 className="text-xl font-semibold mb-6 gradient-text">Research Progress</h3>
      
      <div className="space-y-4">
        {agentSteps.map((step, index) => {
          const status = getStepStatus(step.id);
          const hasError = errors && errors.some(error => error.includes(step.label));
          const isCompleted = status === 'completed';
          const isCurrent = status === 'current';
          
          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`flex items-center space-x-4 p-4 rounded-xl transition-all duration-300 ${
                isCurrent ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30' :
                isCompleted ? 'bg-green-500/10 border border-green-500/20' :
                'bg-gray-800/50 border border-gray-700/30'
              } ${hasError ? 'border-red-500/50 bg-red-500/10' : ''}`}
            >
              <div className="flex-shrink-0">
                {getStepIcon(status, hasError)}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className={`font-medium ${
                    isCurrent ? 'text-blue-400' :
                    isCompleted ? 'text-green-400' :
                    hasError ? 'text-red-400' :
                    'text-gray-400'
                  }`}>
                    {step.label}
                  </span>
                  {isCurrent && (
                    <motion.span
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="text-sm text-blue-400"
                    >
                      In progress...
                    </motion.span>
                  )}
                </div>
                <p className="text-sm text-gray-400 mt-1">{step.description}</p>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

export default AgentProgress;
