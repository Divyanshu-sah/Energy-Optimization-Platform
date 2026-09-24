const API_BASE_URL = '/api';

class ApiService {
  async fetchMachines(params = {}) {
    const queryString = new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined)
    ).toString();
    const url = `${API_BASE_URL}/machines${queryString ? `?${queryString}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch machines');
    return response.json();
  }

  async fetchMachine(machineId) {
    const response = await fetch(`${API_BASE_URL}/machines/${machineId}`);
    if (!response.ok) throw new Error('Failed to fetch machine');
    return response.json();
  }

  async fetchAlerts(params = {}) {
    const queryString = new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined)
    ).toString();
    const url = `${API_BASE_URL}/alerts${queryString ? `?${queryString}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch alerts');
    return response.json();
  }

  async fetchRecommendations(params = {}) {
    const queryString = new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined)
    ).toString();
    const url = `${API_BASE_URL}/recommendations${queryString ? `?${queryString}` : ''}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch recommendations');
    return response.json();
  }

  async fetchDashboardSummary() {
    const response = await fetch(`${API_BASE_URL}/dashboard-summary`);
    if (!response.ok) throw new Error('Failed to fetch dashboard summary');
    return response.json();
  }

  async fetchPlants() {
    const response = await fetch(`${API_BASE_URL}/plants`);
    if (!response.ok) throw new Error('Failed to fetch plants');
    return response.json();
  }

  async simulateScenario(scenario) {
    const response = await fetch(`${API_BASE_URL}/simulate?scenario=${scenario}`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to simulate');
    return response.json();
  }

  async ingestTelemetry(telemetry) {
    const response = await fetch(`${API_BASE_URL}/telemetry/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(telemetry),
    });
    if (!response.ok) throw new Error('Failed to ingest telemetry');
    return response.json();
  }

  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

export const apiService = new ApiService();
export default apiService;
