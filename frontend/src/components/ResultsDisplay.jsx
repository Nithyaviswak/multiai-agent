import { motion, AnimatePresence } from 'framer-motion';
import { fadeIn } from '../animations/fadeIn';
import { staggerChildren } from '../animations/stagger';
import ConfidenceMeter from './ConfidenceMeter';
import PDFExport from './PDFExport';

const ResultsDisplay = ({ researchData, isLoading }) => {
  if (isLoading) {
    return (
      <motion.div {...fadeIn} className="space-y-6">
        {[1, 2, 3].map(i => (
          <div key={i} className="glass-dark rounded-2xl p-6">
            <div className="skeleton h-6 w-1/3 mb-4 rounded"></div>
            <div className="skeleton h-4 w-full mb-2 rounded"></div>
            <div className="skeleton h-4 w-2/3 rounded"></div>
          </div>
        ))}
      </motion.div>
    );
  }

  if (!researchData) return null;

  const {
    summary_data, 
    report_data, 
    fact_check_data,
    fact_check_confidence 
  } = researchData;

  return (
    <motion.div 
      variants={staggerChildren}
      initial="initial"
      animate="animate"
      className="space-y-6"
    >
      {/* Research Summary */}
      <AnimatePresence>
        {summary_data && (
          <motion.div 
            {...fadeIn}
            className="glass-dark rounded-2xl p-6"
          >
            <h3 className="text-xl font-semibold mb-4 gradient-text">Research Summary</h3>
            <div className="prose prose-invert max-w-none">
              <pre className="whitespace-pre-wrap text-gray-300 font-sans">
                {summary_data.summary}
              </pre>
            </div>
            
            {summary_data.key_points && (
              <div className="mt-4">
                <h4 className="font-semibold text-gray-400 mb-2">Key Points:</h4>
                <ul className="space-y-1">
                  {summary_data.key_points.map((point, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="text-green-400 mt-1">-</span>
                      <span className="text-gray-300">{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Final Report */}
      <AnimatePresence>
        {report_data && (
          <motion.div 
            {...fadeIn}
            className="glass-dark rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold gradient-text">Final Report</h3>
              <span className="text-sm text-gray-400">
                {report_data.word_count} words
              </span>
            </div>
            
            <div className="prose prose-invert max-w-none">
              <pre className="whitespace-pre-wrap text-gray-300 font-sans leading-relaxed">
                {report_data.report_content}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Confidence and Export */}
      <AnimatePresence>
        {(fact_check_confidence !== undefined || report_data) && (
          <motion.div 
            {...fadeIn}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {fact_check_confidence !== undefined && (
              <ConfidenceMeter confidence={fact_check_confidence} />
            )}
            
            <PDFExport 
              workflowId={researchData.workflow_id} 
              reportData={report_data}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Fact Check Details */}
      <AnimatePresence>
        {fact_check_data && (
          <motion.div 
            {...fadeIn}
            className="glass-dark rounded-2xl p-6"
          >
            <h3 className="text-xl font-semibold mb-4 gradient-text">Fact Check Details</h3>
            
            <div className="space-y-4">
              {fact_check_data.checked_claims?.map((claim, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`p-4 rounded-lg border ${
                    claim.is_supported 
                      ? 'border-green-500/30 bg-green-500/10' 
                      : 'border-red-500/30 bg-red-500/10'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-medium text-gray-300">{claim.claim}</span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      claim.is_supported ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {claim.is_supported ? 'Supported' : 'Unsupported'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-400 mb-2">{claim.explanation}</p>
                  <div className="text-xs text-gray-500">
                    Confidence: {Math.round(claim.confidence * 100)}%
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default ResultsDisplay;

