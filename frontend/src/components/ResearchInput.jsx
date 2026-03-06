import { motion } from 'framer-motion';
import { Search, Send } from 'lucide-react';
import { useState } from 'react';
import { slideUp } from '../animations/slideUp';

const ResearchInput = ({ onStartResearch, isLoading }) => {
  const [topic, setTopic] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim() && !isLoading) {
      onStartResearch(topic.trim());
    }
  };

  return (
    <motion.div 
      {...slideUp}
      className="glass rounded-2xl p-8 mb-8"
    >
      <div className="text-center mb-6">
        <h1 className="text-4xl font-bold gradient-text mb-2">
          AI Research Assistant
        </h1>
        <p className="text-gray-400">
          Enter a topic to generate a comprehensive research report using AI agents
        </p>
      </div>

      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter research topic (e.g., AI trends in 2024, climate change impacts, etc.)"
            className="w-full pl-12 pr-24 py-4 bg-gray-900/50 border border-gray-700 rounded-xl 
                     text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 
                     focus:ring-2 focus:ring-blue-500/20 transition-all duration-300"
            disabled={isLoading}
          />
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={!topic.trim() || isLoading}
            className={`absolute right-2 top-1/2 transform -translate-y-1/2 px-6 py-2 rounded-lg 
                      transition-all duration-300 flex items-center space-x-2
                      ${!topic.trim() || isLoading 
                        ? 'bg-gray-700 cursor-not-allowed' 
                        : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500'
                      }`}
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>{isLoading ? 'Processing...' : 'Research'}</span>
          </motion.button>
        </div>
        
        {topic.trim() && (
          <motion.p
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="text-sm text-gray-400 mt-3"
          >
            Researching: <span className="text-blue-400">{topic}</span>
          </motion.p>
        )}
      </form>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="glass-dark p-4 rounded-xl text-center"
        >
          <div className="w-8 h-8 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
            <Search className="w-4 h-4 text-blue-400" />
          </div>
          <h4 className="font-semibold mb-1">Research Agent</h4>
          <p className="text-sm text-gray-400">Gathers latest information from web sources</p>
        </motion.div>

        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="glass-dark p-4 rounded-xl text-center"
        >
          <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
            <Send className="w-4 h-4 text-green-400" />
          </div>
          <h4 className="font-semibold mb-1">AI Agents</h4>
          <p className="text-sm text-gray-400">4 specialized agents working together</p>
        </motion.div>

        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="glass-dark p-4 rounded-xl text-center"
        >
          <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
            <span className="text-purple-400 font-bold text-sm">OK</span>
          </div>
          <h4 className="font-semibold mb-1">Fact Checked</h4>
          <p className="text-sm text-gray-400">Verified results with confidence scoring</p>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ResearchInput;

