import { motion } from 'framer-motion';
import { Toaster } from 'react-hot-toast';
import ResearchInput from '../components/ResearchInput';
import AgentProgress from '../components/AgentProgress';
import ResultsDisplay from '../components/ResultsDisplay';
import { useResearch } from '../hooks/useResearch';
import { fadeIn } from '../animations/fadeIn';

const Dashboard = () => {
  const { researchState, startResearch, resetResearch } = useResearch();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a1a1a',
            color: 'white',
            border: '1px solid #333',
          },
        }}
      />
      
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <motion.header 
          {...fadeIn}
          className="text-center mb-12"
        >
          <h1 className="text-5xl md:text-6xl font-bold gradient-text mb-4">
            Multi-Agent AI Research System
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Advanced AI-powered research platform with automated fact-checking and professional report generation
          </p>
        </motion.header>

        {/* Research Input */}
        <ResearchInput 
          onStartResearch={startResearch}
          isLoading={researchState.isLoading}
        />

        {/* Progress Indicator */}
        {researchState.isLoading && researchState.workflowId && (
          <AgentProgress 
            currentStep={researchState.currentStep}
            errors={researchState.data?.errors}
          />
        )}

        {/* Results Display */}
        {(researchState.data || researchState.error) && (
          <ResultsDisplay 
            researchData={researchState.data}
            isLoading={researchState.isLoading}
          />
        )}

        {/* Error State */}
        {researchState.error && !researchState.isLoading && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-dark rounded-2xl p-6 border border-red-500/30"
          >
            <div className="flex items-center space-x-3 text-red-400 mb-4">
              <div className="w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center">
                <span className="text-sm">!</span>
              </div>
              <h3 className="text-lg font-semibold">Research Failed</h3>
            </div>
            <p className="text-gray-300 mb-4">{researchState.error}</p>
            <button
              onClick={resetResearch}
              className="px-6 py-2 bg-red-600/20 border border-red-500/30 rounded-lg 
                       hover:bg-red-600/30 transition-all duration-300"
            >
              Try Again
            </button>
          </motion.div>
        )}

        {/* Footer */}
        <motion.footer 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center mt-16 pt-8 border-t border-gray-800"
        >
          <p className="text-gray-400 text-sm mb-3">
            Developed by <span className="font-semibold text-white">R NITHYANANDACHARI</span>
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4 text-sm">
            <a href="mailto:nviswaks@gmail.com" className="text-gray-400 hover:text-white transition-colors duration-200">
              nviswaks@gmail.com
            </a>
            <a
              href="https://github.com/Nithyaviswak"
              target="_blank"
              rel="noreferrer"
              className="text-gray-400 hover:text-white transition-colors duration-200"
            >
              GitHub
            </a>
            <a
              href="https://www.linkedin.com/in/nithyananda1311"
              target="_blank"
              rel="noreferrer"
              className="text-gray-400 hover:text-white transition-colors duration-200"
            >
              LinkedIn
            </a>
          </div>
        </motion.footer>
      </div>
    </div>
  );
};

export default Dashboard;
