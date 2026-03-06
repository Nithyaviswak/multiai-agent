import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const ConfidenceMeter = ({ confidence = 0 }) => {
  const percentage = Math.round((confidence || 0) * 100);
  const status = percentage >= 80 ? 'high' : percentage >= 60 ? 'medium' : 'low';
  
  const statusConfig = {
    high: { color: 'text-green-400', bg: 'bg-green-500', icon: CheckCircle },
    medium: { color: 'text-yellow-400', bg: 'bg-yellow-500', icon: AlertCircle },
    low: { color: 'text-red-400', bg: 'bg-red-500', icon: XCircle }
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-dark rounded-2xl p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Fact Check Confidence</h3>
        <Icon className={`w-6 h-6 ${config.color}`} />
      </div>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Confidence Score</span>
          <span className={`font-bold ${config.color}`}>{percentage}%</span>
        </div>
        
        <div className="w-full bg-gray-700 rounded-full h-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
            className={`h-3 rounded-full ${config.bg}`}
          />
        </div>
        
        <div className="flex justify-between text-xs text-gray-400">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
        
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className={`text-sm ${config.color} font-medium`}
        >
          {status === 'high' && 'High confidence - Report appears reliable'}
          {status === 'medium' && 'Medium confidence - Some claims need verification'}
          {status === 'low' && 'Low confidence - Significant verification needed'}
        </motion.p>
      </div>
    </motion.div>
  );
};

export default ConfidenceMeter;
