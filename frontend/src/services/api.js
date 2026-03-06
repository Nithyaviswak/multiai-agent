import axios from 'axios';

const API_BASE_URL = '/api';

class ResearchAPI {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  setupInterceptors() {
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  async startResearch(topic) {
    const response = await this.client.post('/research', { topic });
    return response.data;
  }

  async getResearchStatus(workflowId) {
    const response = await this.client.get(`/research/${workflowId}`);
    return response.data;
  }

  async generatePDF(workflowId) {
    const response = await this.client.post(`/generate-pdf/${workflowId}`);
    return response.data;
  }

  async pollResearchStatus(workflowId, interval = 2000, timeout = 120000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const poll = async () => {
        try {
          const result = await this.getResearchStatus(workflowId);
          const step = result.data?.current_step;
          
          if (result.error || result.success === false) {
            resolve(result);
            return;
          }

          if (step === 'complete' || step === 'error') {
            resolve(result);
            return;
          }

          if (Date.now() - startTime > timeout) {
            reject(new Error('Polling timeout'));
            return;
          }

          setTimeout(poll, interval);
        } catch (error) {
          const status = error?.response?.status;
          const elapsed = Date.now() - startTime;

          // Transient 404 can happen right after workflow creation; keep polling until timeout.
          if (status === 404 && elapsed <= timeout) {
            setTimeout(poll, interval);
            return;
          }

          reject(error);
        }
      };

      poll();
    });
  }
}

export const researchAPI = new ResearchAPI();
