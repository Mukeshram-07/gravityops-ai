// --- GravityOps AI Client-side API helper ---

export interface Service {
  id: number;
  name: string;
  criticality: string;
  sla_minutes: number;
}

export interface AlertEvent {
  id: number;
  timestamp: string;
  service_name: string;
  message: string;
  severity: string;
  host: string | null;
  incident_id: number | null;
}

export interface IncidentNote {
  id: number;
  incident_id: number;
  operator_name: string;
  content: string;
  created_at: string;
}

export interface IncidentTimelineEvent {
  id: number;
  incident_id: number;
  timestamp: string;
  event_type: string;
  operator_name: string;
  message: string;
}

export interface Incident {
  id: number;
  title: string;
  service_id: number;
  status: string;
  severity: string;
  sla_risk: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  sla_deadline: string;
  predicted_severity: string | null;
  predicted_root_cause: string | null;
  service: Service;
}

export interface IncidentDetail extends Incident {
  alerts: AlertEvent[];
  notes: IncidentNote[];
  timeline: IncidentTimelineEvent[];
}

export interface UploadJob {
  id: string;
  filename: string;
  status: string;
  alerts_count: number;
  created_at: string;
  error_message: string | null;
}

export interface SeverityMix {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface StatusMix {
  open: number;
  investigating: number;
  mitigated: number;
  resolved: number;
}

export interface SlaRiskMix {
  healthy: number;
  watch: number;
  at_risk: number;
  breach_likely: number;
}

export interface ServiceNoisyMetric {
  service_name: string;
  alert_count: number;
  incident_count: number;
  mttr_minutes: number;
}

export interface DailyOutageTrend {
  date: string;
  count: number;
}

export interface AnalyticsOverview {
  total_incidents: number;
  active_incidents: number;
  resolved_incidents: number;
  mttr_minutes: number;
  sla_breach_rate: number;
  severity_mix: SeverityMix;
  status_mix: StatusMix;
  sla_risk_mix: SlaRiskMix;
  noisy_services: ServiceNoisyMetric[];
  daily_trends: DailyOutageTrend[];
}

export interface IncidentFilters {
  status?: string;
  severity?: string;
  service?: string;
  sla_risk?: string;
  search?: string;
}

const API_BASE = '/api';

export const api = {
  /**
   * Fetches incidents from database with optional filters
   */
  async getIncidents(filters: IncidentFilters = {}): Promise<Incident[]> {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.service) params.append('service', filters.service);
    if (filters.sla_risk) params.append('sla_risk', filters.sla_risk);
    if (filters.search) params.append('search', filters.search);

    const res = await fetch(`${API_BASE}/incidents?${params.toString()}`);
    if (!res.ok) {
      throw new Error(`Failed to load incidents: ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Fetches full incident details (including alerts, notes, timeline)
   */
  async getIncidentDetail(id: number): Promise<IncidentDetail> {
    const res = await fetch(`${API_BASE}/incidents/${id}`);
    if (!res.ok) {
      throw new Error(`Failed to load incident detail for ID ${id}: ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Updates status, severity, or manual SLA risk overrides on an incident
   */
  async updateIncident(
    id: number,
    updateData: { status?: string; severity?: string; sla_risk?: string },
    operator: string = 'SRE Operator'
  ): Promise<Incident> {
    const res = await fetch(`${API_BASE}/incidents/${id}?operator=${encodeURIComponent(operator)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to update incident: ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Adds an operator comment note to an incident
   */
  async addIncidentNote(
    id: number,
    noteData: { operator_name: string; content: string }
  ): Promise<IncidentNote> {
    const res = await fetch(`${API_BASE}/incidents/${id}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(noteData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to submit note: ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Queries high-level SRE analytics summary
   */
  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    if (!res.ok) {
      throw new Error(`Failed to fetch analytics: ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Uploads raw alert log files (CSV or JSON)
   */
  async uploadAlerts(file: File): Promise<UploadJob> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/incidents/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to upload logs: ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Checks upload status for a job ID
   */
  async getUploadStatus(jobId: string): Promise<UploadJob> {
    const res = await fetch(`${API_BASE}/uploads/${jobId}`);
    if (!res.ok) {
      throw new Error(`Failed to check upload job status: ${res.statusText}`);
    }
    return res.json();
  },

  /**
   * Fetches the ML classifier diagnostics
   */
  async getMlDiagnostics(): Promise<{ mode: string; training_sample_count: number }> {
    const res = await fetch(`${API_BASE}/ml/diagnostics`);
    if (!res.ok) {
      throw new Error(`Failed to fetch ML diagnostics: ${res.statusText}`);
    }
    return res.json();
  }
};
