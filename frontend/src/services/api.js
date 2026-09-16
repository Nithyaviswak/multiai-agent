import axios from 'axios';

const API_BASE_URL = '/api';

class TravelAPI {
  constructor() {
    this.client = axios.create({ baseURL: API_BASE_URL, timeout: 30000, headers: { 'Content-Type': 'application/json' } });
    this.setupInterceptors();
  }

  setupInterceptors() {
    this.client.interceptors.response.use(r => r, e => { console.error('API Error:', e.response?.data || e.message); return Promise.reject(e); });
  }

  async startTravelWorkflow(intent, options = {}, sessionId = 'default', userId = 'engineer') {
    const payload = {
      intent,
      origin: options.origin || null,
      destination: options.destination || null,
      travel_modes: options.travel_modes || null,
      meal_types: options.meal_types || null,
      time_budget_minutes: options.time_budget_minutes || null,
      preferences: options.preferences || null,
      session_id: sessionId,
      user_id: userId,
    };
    const r = await this.client.post('/travel', payload);
    return r.data;
  }

  async getTravelResult(workflowId) {
    const r = await this.client.get(`/travel/${workflowId}`);
    return r.data;
  }

  async getMapsStatus() {
    const r = await this.client.get('/maps/status');
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

  async getModels() {
    const r = await this.client.get('/models');
    return r.data;
  }

  async getCurrentModel() {
    const r = await this.client.get('/models/current');
    return r.data;
  }

  async setModel(model) {
    const r = await this.client.post('/models', { model });
    return r.data;
  }

  async getProviders() {
    const r = await this.client.get('/providers');
    return r.data;
  }

  async setProviderKey(provider, key) {
    const r = await this.client.post('/providers/keys', { provider, key });
    return r.data;
  }

  async getBaseUrls() {
    const r = await this.client.get('/models/base-urls');
    return r.data;
  }

  async addCustomModel(name, modelId, apiKey, baseUrl) {
    const r = await this.client.post('/models/custom', { name, model_id: modelId, api_key: apiKey, base_url: baseUrl });
    return r.data;
  }

  async removeCustomModel(modelId) {
    const r = await this.client.delete('/models/custom', { params: { model_id: modelId } });
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
          const result = await this.getTravelResult(workflowId);
          const step = result.data?.current_step;
          if (result.error || result.success === false) { resolve(result); return; }
          if (step === 'complete' || step === 'error') { resolve(result); return; }
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

export const travelAPI = new TravelAPI();