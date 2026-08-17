import axios from 'axios';

const API_BASE_URL = '/api';

class NetworkAPI {
  constructor() {
    this.client = axios.create({ baseURL: API_BASE_URL, timeout: 30000, headers: { 'Content-Type': 'application/json' } });
    this.setupInterceptors();
  }

  setupInterceptors() {
    this.client.interceptors.request.use(c => { console.log(`API: ${c.method?.toUpperCase()} ${c.url}`); return c; }, e => Promise.reject(e));
    this.client.interceptors.response.use(r => r, e => { console.error('API Error:', e.response?.data || e.message); return Promise.reject(e); });
  }

  async startNetworkWorkflow(intent, environment = 'devnet-sandbox', sessionId = 'default', userId = 'engineer') {
    const r = await this.client.post('/network', { intent, environment, session_id: sessionId, user_id: userId });
    return r.data;
  }

  async getWorkflowStatus(workflowId) {
    const r = await this.client.get(`/network/${workflowId}`);
    return r.data;
  }

  async approveAction(workflowId, approved, userId = 'engineer') {
    const r = await this.client.post('/approve', { workflow_id: workflowId, approved, user_id: userId });
    return r.data;
  }

  async getMemoryHistory(sessionId) {
    const r = await this.client.post('/memory/history', { session_id: sessionId });
    return r.data;
  }

  async getMemoryContext(sessionId) {
    const r = await this.client.post('/memory/context', { session_id: sessionId });
    return r.data;
  }

  async undoLastChange(sessionId) {
    const r = await this.client.post('/memory/undo', { session_id: sessionId });
    return r.data;
  }

  async getDevices() {
    const r = await this.client.get('/devices');
    return r.data;
  }

  async getTopology() {
    const r = await this.client.get('/topology');
    return r.data;
  }

  async listTools() {
    const r = await this.client.get('/tools/list');
    return r.data;
  }

  async callTool(tool, params) {
    const r = await this.client.post('/tools/call', { tool, params });
    return r.data;
  }

  async getEvalStats(agent = null) {
    const r = await this.client.get('/evaluation/stats', { params: agent ? { agent } : {} });
    return r.data;
  }

  async getAuditLogs(limit = 100, action = null) {
    const r = await this.client.get('/audit/logs', { params: { limit, ...(action ? { action } : {}) } });
    return r.data;
  }

  async getAuditStats() {
    const r = await this.client.get('/audit/stats');
    return r.data;
  }

  async pollWorkflowStatus(workflowId, interval = 2000, timeout = 180000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const poll = async () => {
        try {
          const result = await this.getWorkflowStatus(workflowId);
          const step = result.data?.current_step;
          if (result.error || result.success === false) { resolve(result); return; }
          if (step === 'complete' || step === 'error' || step === 'awaiting_approval' || step === 'approved' || step === 'denied') { resolve(result); return; }
          if (Date.now() - startTime > timeout) { reject(new Error('Polling timeout')); return; }
          setTimeout(poll, interval);
        } catch (error) {
          const status = error?.response?.status;
          if (status === 404 && Date.now() - startTime <= timeout) { setTimeout(poll, interval); return; }
          reject(error);
        }
      };
      poll();
    });
  }
}

export const networkAPI = new NetworkAPI();
