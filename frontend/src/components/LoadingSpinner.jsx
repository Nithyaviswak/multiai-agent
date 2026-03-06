import { motion } from 'framer-motion';
import { fadeIn } from '../animations/fadeIn';

const LoadingSpinner = ({ size = 'md', text = 'Processing...' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <motion.div 
      {...fadeIn}
      className="flex flex-col items-center justify-center space-y-4"
    >
      <div className={`${sizes[size]} relative`}>
        <div className="absolute inset-0 rounded-full border-2 border-gray-600"></div>
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-blue-500 border-t-transparent"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
      </div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-gray-400 text-sm font-medium"
      >
        {text}
      </motion.p>
    </motion.div>
  );
};

export default LoadingSpinner;
