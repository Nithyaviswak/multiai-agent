import { motion } from 'framer-motion';
import { Download, Clipboard, CheckCircle } from 'lucide-react';
import { useState } from 'react';
import { researchAPI } from '../services/api';
import toast from 'react-hot-toast';

const PDFExport = ({ workflowId, reportData }) => {
  const [isCopying, setIsCopying] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleCopyToClipboard = async () => {
    if (!reportData?.report_content) return;
    
    setIsCopying(true);
    try {
      await navigator.clipboard.writeText(reportData.report_content);
      toast.success('Report copied to clipboard!');
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    } finally {
      setIsCopying(false);
    }
  };

  const handleExportPDF = async () => {
    if (!workflowId) return;
    
    setIsExporting(true);
    try {
      const response = await researchAPI.generatePDF(workflowId);
      
      if (response.success) {
        // Create download link
        const link = document.createElement('a');
        link.href = `data:application/pdf;base64,${response.pdf_data}`;
        link.download = `research-report-${workflowId}.pdf`;
        link.click();
        toast.success('PDF downloaded successfully!');
      }
    } catch (error) {
      toast.error('Failed to generate PDF');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-dark rounded-2xl p-6"
    >
      <h3 className="text-lg font-semibold mb-4">Export Options</h3>
      
      <div className="flex flex-col sm:flex-row gap-4">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleCopyToClipboard}
          disabled={isCopying || !reportData}
          className="flex items-center justify-center space-x-2 px-6 py-3 bg-blue-600/20 
                   border border-blue-500/30 rounded-xl hover:bg-blue-600/30 
                   transition-all duration-300 disabled:opacity-50"
        >
          {isCopying ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Clipboard className="w-4 h-4" />
          )}
          <span>{isCopying ? 'Copying...' : 'Copy to Clipboard'}</span>
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleExportPDF}
          disabled={isExporting || !workflowId}
          className="flex items-center justify-center space-x-2 px-6 py-3 bg-purple-600/20 
                   border border-purple-500/30 rounded-xl hover:bg-purple-600/30 
                   transition-all duration-300 disabled:opacity-50"
        >
          {isExporting ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          <span>{isExporting ? 'Exporting...' : 'Export as PDF'}</span>
        </motion.button>
      </div>

      {reportData?.fact_check_confidence && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg"
        >
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-sm text-green-400">
              Report ready with {Math.round(reportData.fact_check_confidence * 100)}% confidence
            </span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default PDFExport;
