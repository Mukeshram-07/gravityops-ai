import React, { useState, useEffect, useRef } from 'react';
import { 
  AlertTriangle, 
  Activity, 
  BarChart2, 
  Upload, 
  CheckCircle, 
  Clock, 
  ShieldAlert, 
  Search, 
  X, 
  Server, 
  AlertCircle,
  Database,
  Terminal,
  Sun,
  Moon,
  ChevronRight
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell
} from 'recharts';
import { api, Incident, IncidentDetail, UploadJob, AnalyticsOverview } from './lib/api';

const RECOMMENDATION_MAP: Record<string, string[]> = {
  "deployment regression": [
    "Verify git commit logs and recent CI/CD pipeline runs for deployment regression.",
    "Locate the deployed container version tag and trigger a rollback if service latency persists.",
    "Check release documentation or verify deployment signature validations."
  ],
  "dependency timeout": [
    "Verify downstream and third-party API gateway health status.",
    "Inspect the database connection pool settings and review locking logs.",
    "Check network latency spikes and check request timeout configurations."
  ],
  "schema drift": [
    "Identify recent database schema migrations or catalog changes.",
    "Verify column types or schema mappings on the consumer payload parsing layer.",
    "Reparse blocked/failed messages from queue history."
  ],
  "infrastructure saturation": [
    "Inspect CPU/Memory usage metrics on Kubernetes replica pods.",
    "Scale container instances to absorb traffic load (horizontal pod autoscaling).",
    "Verify resource allocation limits and check for OOM (Out Of Memory) events."
  ],
  "message queue backlog": [
    "Scale worker pools to accelerate queue draining rate.",
    "Analyze dead-letter queue (DLQ) payloads for validation failures.",
    "Throttling producers temporarily to allow consumers to recover."
  ],
  "credential rotation issue": [
    "Check key validation/decryption certificates expiration schedules.",
    "Audit vault secrets and confirm permissions on API key validation layers.",
    "Re-run auto-renewal triggers or perform manual credential generation."
  ],
  "cache invalidation bug": [
    "Query cache hit/miss ratio metrics and evictions on Redis instances.",
    "Perform manual cache invalidation of stale keys via administrator CLI.",
    "Verify cache key naming collisions or serialization formats."
  ],
  "third-party provider degradation": [
    "Check Stripe, AWS, SendGrid or remote provider official status dashboards.",
    "Enable automated secondary fallback routes if provider outages continue.",
    "Notify operations management to communicate outage timelines to customers."
  ]
};

const PRESET_OPERATORS = [
  { name: "Alex Rivers", role: "SRE Team Lead", avatar: "👨‍💻" },
  { name: "Elena Rostova", role: "On-call SRE Engineer", avatar: "👩‍💻" },
  { name: "Marcus Vance", role: "Operations Director", avatar: "🧑‍💼" }
];

export default function App() {
  // Navigation State
  const [activeTab, setActiveTab] = useState<'dashboard' | 'analytics' | 'upload'>('dashboard');
  const [isDarkMode, setIsDarkMode] = useState<boolean>(true);

  // Data States
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<IncidentDetail | null>(null);
  const [mlDiagnostics, setMlDiagnostics] = useState<{ mode: string; training_sample_count: number } | null>(null);
  
  // Filtering States
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [serviceFilter, setServiceFilter] = useState('');
  const [slaRiskFilter, setSlaRiskFilter] = useState('');
  
  // Loading & Error States
  const [loadingIncidents, setLoadingIncidents] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Upload States
  const [uploadJobs, setUploadJobs] = useState<UploadJob[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Note State
  const [newNote, setNewNote] = useState('');
  const [submittingNote, setSubmittingNote] = useState(false);

  // Operator Session States
  const [currentOperator, setCurrentOperator] = useState<string | null>(null);
  const [currentRole, setCurrentRole] = useState<string | null>(null);

  const operatorName = currentOperator ? `${currentOperator} (${currentRole})` : "Guest Operator";

  // Load active session on mount
  useEffect(() => {
    const saved = localStorage.getItem("gravityops_operator");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setCurrentOperator(parsed.name);
        setCurrentRole(parsed.role);
      } catch (err) {
        console.error("Failed to parse operator session", err);
      }
    }
  }, []);

  // Toast Notification State
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Toggle Theme
  const toggleTheme = () => {
    const nextDark = !isDarkMode;
    setIsDarkMode(nextDark);
    if (nextDark) {
      document.body.classList.remove('light-theme');
    } else {
      document.body.classList.add('light-theme');
    }
  };

  // Fetch Incidents
  const fetchIncidents = async () => {
    setLoadingIncidents(true);
    try {
      const data = await api.getIncidents({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        service: serviceFilter || undefined,
        sla_risk: slaRiskFilter || undefined,
        search: searchQuery || undefined
      });
      setIncidents(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to retrieve incidents');
    } finally {
      setLoadingIncidents(false);
    }
  };

  // Fetch Analytics
  const fetchAnalytics = async () => {
    setLoadingAnalytics(true);
    try {
      const data = await api.getAnalyticsOverview();
      setAnalytics(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoadingAnalytics(false);
    }
  };

  // Fetch Incident Details
  const fetchIncidentDetail = async (id: number) => {
    setLoadingDetail(true);
    try {
      const data = await api.getIncidentDetail(id);
      setSelectedIncident(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to load details', 'error');
    } finally {
      setLoadingDetail(false);
    }
  };

  // Fetch ML Diagnostics
  const fetchMlDiagnostics = async () => {
    try {
      const data = await api.getMlDiagnostics();
      setMlDiagnostics(data);
    } catch (err) {
      console.error("Failed to load ML diagnostics", err);
    }
  };

  // Initial Data Fetch
  useEffect(() => {
    fetchIncidents();
    fetchAnalytics();
    fetchMlDiagnostics();
  }, [statusFilter, severityFilter, serviceFilter, slaRiskFilter]);

  // Handle Search Input Debounce / Action
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchIncidents();
  };

  // Clear Filters
  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('');
    setSeverityFilter('');
    setServiceFilter('');
    setSlaRiskFilter('');
    // State updates will trigger fetchIncidents via dependency array or manual invoke:
    setTimeout(() => {
      fetchIncidents();
    }, 0);
  };

  // Open Incident Details
  const handleSelectIncident = (id: number) => {
    setSelectedIncidentId(id);
    fetchIncidentDetail(id);
  };

  // Update Status / Severity from Details Panel
  const handleUpdateStatus = async (statusVal: string) => {
    if (!selectedIncidentId) return;
    try {
      await api.updateIncident(selectedIncidentId, { status: statusVal }, operatorName);
      showToast(`Incident status updated to ${statusVal.toUpperCase()}`);
      fetchIncidents();
      fetchIncidentDetail(selectedIncidentId);
      fetchAnalytics();
    } catch (err: any) {
      showToast(err.message || 'Failed to update status', 'error');
    }
  };

  const handleUpdateSeverity = async (sevVal: string) => {
    if (!selectedIncidentId) return;
    try {
      await api.updateIncident(selectedIncidentId, { severity: sevVal }, operatorName);
      showToast(`Incident severity modified to ${sevVal.toUpperCase()}`);
      fetchIncidents();
      fetchIncidentDetail(selectedIncidentId);
      fetchAnalytics();
    } catch (err: any) {
      showToast(err.message || 'Failed to update severity', 'error');
    }
  };

  const handleUpdateSlaRisk = async (riskVal: string) => {
    if (!selectedIncidentId) return;
    try {
      await api.updateIncident(selectedIncidentId, { sla_risk: riskVal }, operatorName);
      showToast(`Incident SLA Risk set to ${riskVal.toUpperCase()}`);
      fetchIncidents();
      fetchIncidentDetail(selectedIncidentId);
      fetchAnalytics();
    } catch (err: any) {
      showToast(err.message || 'Failed to update SLA Risk', 'error');
    }
  };

  // Submit Note
  const handleSubmitNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim() || !selectedIncidentId) return;
    setSubmittingNote(true);
    try {
      await api.addIncidentNote(selectedIncidentId, {
        operator_name: operatorName,
        content: newNote.trim()
      });
      setNewNote('');
      showToast("Note added successfully");
      fetchIncidentDetail(selectedIncidentId);
    } catch (err: any) {
      showToast(err.message || 'Failed to add note', 'error');
    } finally {
      setSubmittingNote(false);
    }
  };

  // File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    showToast(`Uploading alert log: ${file.name}`);
    try {
      const job = await api.uploadAlerts(file);
      setUploadJobs(prev => [job, ...prev]);
      
      // Start polling the job status
      pollJobStatus(job.id);
    } catch (err: any) {
      showToast(err.message || 'Outage log upload failed', 'error');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Poll Job Status
  const pollJobStatus = (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const job = await api.getUploadStatus(jobId);
        // Update jobs list
        setUploadJobs(prev => prev.map(j => j.id === jobId ? job : j));
        
        if (job.status === 'completed') {
          clearInterval(interval);
          showToast(`Ingestion completed: ${job.alerts_count} alerts normalized and clusters updated.`);
          fetchIncidents();
          fetchAnalytics();
          fetchMlDiagnostics();
        } else if (job.status === 'failed') {
          clearInterval(interval);
          showToast(`Ingestion failed: ${job.error_message}`, 'error');
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 2000);
  };

  // Trigger file click
  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  // Format date helper
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };


  const STATUS_COLORS = {
    open: '#ef4444',
    investigating: '#f59e0b',
    mitigated: '#3b82f6',
    resolved: '#10b981'
  };

  // Fetch analytics if switching tabs
  const handleTabChange = (tab: 'dashboard' | 'analytics' | 'upload') => {
    setActiveTab(tab);
    if (tab === 'analytics') {
      fetchAnalytics();
    }
  };

  if (!currentOperator) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#0b0c0f',
        fontFamily: 'var(--font-sans)',
        padding: '2rem'
      }}>
        <div className="chart-card" style={{
          maxWidth: '450px',
          width: '100%',
          padding: '2.5rem',
          border: '1px solid var(--border-color)',
          background: 'linear-gradient(135deg, #171a21 0%, #0f1115 100%)',
          boxShadow: 'var(--shadow-lg)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.5rem'
        }}>
          <div style={{ textAlign: 'center' }}>
            <h1 style={{ fontSize: '1.75rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontWeight: 700 }}>
              ⚡ Gravity<span style={{ color: 'var(--accent-color)' }}>Ops AI</span>
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
              Operational Incident Command Center Login
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
              Select Active Operator Profile
            </span>
            {PRESET_OPERATORS.map((op) => (
              <div 
                key={op.name}
                onClick={() => {
                  const session = { name: op.name, role: op.role };
                  localStorage.setItem("gravityops_operator", JSON.stringify(session));
                  setCurrentOperator(op.name);
                  setCurrentRole(op.role);
                  showToast(`Session active: Logged in as ${op.name}`);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  padding: '1rem',
                  backgroundColor: 'var(--bg-base)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  transition: 'var(--transition)',
                }}
                className="operator-row-hover"
              >
                <span style={{ fontSize: '1.5rem' }}>{op.avatar}</span>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <strong style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>{op.name}</strong>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>{op.role}</span>
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
            <div style={{ flexGrow: 1, height: '1px', backgroundColor: 'var(--border-color)' }}></div>
            <span style={{ fontSize: '0.7rem', textTransform: 'uppercase' }}>Or Custom Input</span>
            <div style={{ flexGrow: 1, height: '1px', backgroundColor: 'var(--border-color)' }}></div>
          </div>

          <form onSubmit={(e) => {
            e.preventDefault();
            const form = e.currentTarget;
            const name = (form.elements.namedItem("op_name") as HTMLInputElement).value.trim();
            if (!name) return;
            const session = { name: name, role: "Guest Operator" };
            localStorage.setItem("gravityops_operator", JSON.stringify(session));
            setCurrentOperator(name);
            setCurrentRole("Guest Operator");
            showToast(`Session active: Logged in as ${name}`);
          }} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <input 
              name="op_name"
              type="text" 
              className="search-input" 
              style={{ paddingLeft: '1rem' }} 
              placeholder="Operator name..." 
              required 
            />
            <button type="submit" className="btn btn-primary" style={{ justifyContent: 'center' }}>
              Access Command Center
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            ⚡ Gravity<span>Ops AI</span>
          </div>
        </div>
        
        <ul className="sidebar-menu">
          <li>
            <div 
              className={`sidebar-item ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => handleTabChange('dashboard')}
            >
              <Activity size={18} />
              Triage Workspace
            </div>
          </li>
          <li>
            <div 
              className={`sidebar-item ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => handleTabChange('analytics')}
            >
              <BarChart2 size={18} />
              Operations Analytics
            </div>
          </li>
          <li>
            <div 
              className={`sidebar-item ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => handleTabChange('upload')}
            >
              <Upload size={18} />
              Alert Ingestor
            </div>
          </li>
        </ul>
        
        <div className="sidebar-footer" style={{ gap: '0.75rem' }}>
          <div>Environment: Production</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.15rem', backgroundColor: 'rgba(255,255,255,0.03)', padding: '0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(255,255,255,0.05)' }}>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Active Operator:</span>
            <strong style={{ color: '#ffffff', fontSize: '0.85rem' }}>{currentOperator}</strong>
            <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>{currentRole}</span>
          </div>
          <button 
            onClick={() => {
              localStorage.removeItem("gravityops_operator");
              setCurrentOperator(null);
              setCurrentRole(null);
              showToast("Logged out of SRE session");
            }}
            style={{
              background: 'none',
              border: '1px solid rgba(255,255,255,0.15)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.3rem 0.5rem',
              fontSize: '10px',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              textAlign: 'center',
              width: '100%',
              transition: 'var(--transition)'
            }}
            className="operator-logout-btn"
          >
            Switch Operator
          </button>
          <div style={{ fontSize: '10px' }}>v1.2.0-secure</div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="content-wrapper">
        {/* Top Navbar */}
        <header className="topbar">
          <h2 className="topbar-title">
            {activeTab === 'dashboard' && 'Active Incidents Dashboard'}
            {activeTab === 'analytics' && 'Operational Analytics & MTTR'}
            {activeTab === 'upload' && 'Raw Alert Ingestion Pipeline'}
          </h2>
          <div className="topbar-actions">
            <button className="theme-toggle-btn" onClick={toggleTheme} title="Toggle Theme mode">
              {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
              <div style={{ width: '8px', height: '8px', backgroundColor: '#10b981', borderRadius: '50%' }}></div>
              <span>API Gateway Connected</span>
            </div>
          </div>
        </header>

        {/* Dynamic Main Page Content */}
        <main className="main-content">
          {/* Dashboard View */}
          {activeTab === 'dashboard' && (
            <>
              {errorMsg && (
                <div style={{
                  padding: '1rem',
                  backgroundColor: 'var(--color-error-bg)',
                  border: '1px solid var(--color-error)',
                  color: 'var(--color-error)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '1.5rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.9rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <AlertCircle size={18} />
                    <span>{errorMsg}</span>
                  </div>
                  <button 
                    onClick={() => setErrorMsg(null)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-error)' }}
                  >
                    <X size={16} />
                  </button>
                </div>
              )}

              {/* KPI Cards Grid */}
              <section className="kpi-grid">
                <div className="kpi-card error">
                  <span className="kpi-label">Active Incidents</span>
                  <span className="kpi-value">{loadingIncidents ? '...' : incidents.filter(i => i.status !== 'resolved').length}</span>
                  <span className="kpi-footer"><AlertTriangle size={12} /> Requiring operator attention</span>
                </div>
                <div className="kpi-card warning">
                  <span className="kpi-label">Critical Outages</span>
                  <span className="kpi-value">{loadingIncidents ? '...' : incidents.filter(i => i.status !== 'resolved' && i.severity === 'critical').length}</span>
                  <span className="kpi-footer"><ShieldAlert size={12} /> High impact / SLA breach threat</span>
                </div>
                <div className="kpi-card success">
                  <span className="kpi-label">System MTTR</span>
                  <span className="kpi-value">{analytics ? `${analytics.mttr_minutes}m` : '0m'}</span>
                  <span className="kpi-footer"><Clock size={12} /> Average resolution duration</span>
                </div>
                <div className="kpi-card accent">
                  <span className="kpi-label">SLA Breach Rate</span>
                  <span className="kpi-value">{analytics ? `${analytics.sla_breach_rate}%` : '0%'}</span>
                  <span className="kpi-footer"><ShieldAlert size={12} /> Breaches against SLA target</span>
                </div>
              </section>

              {/* ML Diagnostics Banner */}
              {mlDiagnostics && (
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.04) 0%, rgba(59, 130, 246, 0.04) 100%)',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1rem 1.5rem',
                  fontSize: '0.85rem',
                  boxShadow: 'var(--shadow-sm)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Database size={16} style={{ color: 'var(--accent-color)' }} />
                    <div>
                      <strong style={{ color: 'var(--text-primary)' }}>ML Diagnostics: </strong>
                      <span style={{ color: 'var(--text-secondary)' }}>
                        System is operating in{' '}
                        <span style={{ 
                          color: mlDiagnostics.mode === 'trained' ? 'var(--color-success)' : 'var(--color-warning)', 
                          fontWeight: 600 
                        }}>
                          {mlDiagnostics.mode === 'trained' ? 'Trained Model Mode (Multinomial Naive Bayes)' : 'Rule-Based Fallback Mode (Cold Start)'}
                        </span>
                      </span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--text-muted)' }}>
                    <span>Training Samples: <strong style={{ color: 'var(--text-secondary)' }}>{mlDiagnostics.training_sample_count}</strong></span>
                    <span style={{ 
                      width: '8px', 
                      height: '8px', 
                      backgroundColor: mlDiagnostics.mode === 'trained' ? 'var(--color-success)' : 'var(--color-warning)', 
                      borderRadius: '50%',
                      boxShadow: mlDiagnostics.mode === 'trained' 
                        ? '0 0 8px var(--color-success)' 
                        : '0 0 8px var(--color-warning)'
                    }}></span>
                  </div>
                </div>
              )}

              {/* Incidents Table Layout */}
              <section className="table-container">
                {/* Filters Row */}
                <div className="filter-bar">
                  <form onSubmit={handleSearchSubmit} className="search-input-wrapper">
                    <Search size={16} className="search-icon" />
                    <input 
                      type="text" 
                      className="search-input" 
                      placeholder="Search title, services, root cause..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </form>

                  <div className="filter-group">
                    <select 
                      className="select-filter" 
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                    >
                      <option value="">All Statuses</option>
                      <option value="open">Open</option>
                      <option value="investigating">Investigating</option>
                      <option value="mitigated">Mitigated</option>
                      <option value="resolved">Resolved</option>
                    </select>

                    <select 
                      className="select-filter" 
                      value={severityFilter}
                      onChange={(e) => setSeverityFilter(e.target.value)}
                    >
                      <option value="">All Severities</option>
                      <option value="critical">Critical</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>

                    <select 
                      className="select-filter" 
                      value={slaRiskFilter}
                      onChange={(e) => setSlaRiskFilter(e.target.value)}
                    >
                      <option value="">All SLA Risk</option>
                      <option value="healthy">Healthy</option>
                      <option value="watch">Watch</option>
                      <option value="at-risk">At Risk</option>
                      <option value="breach-likely">Breach Likely</option>
                    </select>

                    <button className="btn btn-secondary" onClick={clearFilters}>Reset Filters</button>
                  </div>
                </div>

                {/* Table Data */}
                {loadingIncidents ? (
                  <div style={{ padding: '3rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div className="loading-skeleton" style={{ width: '100%' }}></div>
                    <div className="loading-skeleton" style={{ width: '100%' }}></div>
                    <div className="loading-skeleton" style={{ width: '100%' }}></div>
                    <div className="loading-skeleton" style={{ width: '100%' }}></div>
                  </div>
                ) : incidents.length === 0 ? (
                  <div className="empty-state">
                    <AlertTriangle className="empty-state-icon" />
                    <h3>No incidents match the filters</h3>
                    <p>Modify search keywords or reload database telemetry.</p>
                    <button className="btn btn-secondary" onClick={fetchIncidents}>Reload Data</button>
                  </div>
                ) : (
                  <table className="incident-table">
                    <thead>
                      <tr>
                        <th>Incident Context</th>
                        <th>Severity</th>
                        <th>Status</th>
                        <th>SLA Threat</th>
                        <th>Triggered Time</th>
                        <th>SLA Deadline</th>
                      </tr>
                    </thead>
                    <tbody>
                      {incidents.map((inc) => (
                        <tr key={inc.id} className="incident-row" onClick={() => handleSelectIncident(inc.id)}>
                          <td>
                            <div className="incident-title-cell">
                              <span className="incident-title-text">{inc.title}</span>
                              <span className="incident-service-tag">{inc.service.name} • {inc.service.criticality.toUpperCase()}</span>
                            </div>
                          </td>
                          <td>
                            <span className={`badge badge-sev-${inc.severity.toLowerCase()}`}>
                              {inc.severity}
                            </span>
                          </td>
                          <td>
                            <span className={`badge badge-status-${inc.status.toLowerCase()}`}>
                              {inc.status}
                            </span>
                          </td>
                          <td>
                            <span className={`badge badge-risk-${inc.sla_risk.toLowerCase()}`}>
                              {inc.sla_risk.replace('-', ' ')}
                            </span>
                          </td>
                          <td style={{ color: 'var(--text-secondary)' }}>
                            {formatDate(inc.created_at)}
                          </td>
                          <td style={{ color: 'var(--text-secondary)' }}>
                            {formatDate(inc.sla_deadline)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </section>
            </>
          )}

          {/* Analytics View */}
          {activeTab === 'analytics' && (
            <>
              {loadingAnalytics || !analytics ? (
                <div style={{ padding: '3rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="loading-skeleton" style={{ width: '80%' }}></div>
                  <div className="loading-skeleton" style={{ width: '100%', height: '200px' }}></div>
                </div>
              ) : (
                <>
                  {/* Summary Metric Strip */}
                  <div className="kpi-grid">
                    <div className="kpi-card">
                      <span className="kpi-label">Total Outages Tracked</span>
                      <span className="kpi-value">{analytics.total_incidents}</span>
                      <span className="kpi-footer">Cumulative across telemetry history</span>
                    </div>
                    <div className="kpi-card">
                      <span className="kpi-label">Active / Mitigated</span>
                      <span className="kpi-value">{analytics.active_incidents}</span>
                      <span className="kpi-footer">Currently unresolved in queue</span>
                    </div>
                    <div className="kpi-card">
                      <span className="kpi-label">Mean Resolution Time</span>
                      <span className="kpi-value">{analytics.mttr_minutes} min</span>
                      <span className="kpi-footer">MTTR average for SRE team</span>
                    </div>
                    <div className="kpi-card">
                      <span className="kpi-label">SLA Violation Rate</span>
                      <span className="kpi-value">{analytics.sla_breach_rate}%</span>
                      <span className="kpi-footer">Target SLA breaching instances</span>
                    </div>
                  </div>

                  {/* Charts Layout */}
                  <div className="analytics-grid">
                    <div className="chart-card">
                      <h3 className="section-title">Outage Frequencies (Last 10 Days)</h3>
                      <div className="chart-wrapper">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={analytics.daily_trends}>
                            <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} />
                            <YAxis stroke="var(--text-muted)" fontSize={11} allowDecimals={false} />
                            <Tooltip 
                              contentStyle={{ 
                                backgroundColor: 'var(--bg-surface)', 
                                borderColor: 'var(--border-color)',
                                color: 'var(--text-primary)'
                              }} 
                            />
                            <Line 
                              type="monotone" 
                              dataKey="count" 
                              stroke="var(--accent-color)" 
                              strokeWidth={3} 
                              dot={{ r: 4 }} 
                              activeDot={{ r: 6 }} 
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="chart-card">
                      <h3 className="section-title">Incident Status Mix</h3>
                      <div className="chart-wrapper" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <ResponsiveContainer width="100%" height="80%">
                          <PieChart>
                            <Pie
                              data={[
                                { name: 'Open', value: analytics.status_mix.open },
                                { name: 'Investigating', value: analytics.status_mix.investigating },
                                { name: 'Mitigated', value: analytics.status_mix.mitigated },
                                { name: 'Resolved', value: analytics.status_mix.resolved }
                              ].filter(d => d.value > 0)}
                              cx="50%"
                              cy="50%"
                              innerRadius={60}
                              outerRadius={80}
                              paddingAngle={5}
                              dataKey="value"
                            >
                              <Cell fill={STATUS_COLORS.open} />
                              <Cell fill={STATUS_COLORS.investigating} />
                              <Cell fill={STATUS_COLORS.mitigated} />
                              <Cell fill={STATUS_COLORS.resolved} />
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', justifyContent: 'center', fontSize: '0.75rem', marginTop: '0.5rem' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: STATUS_COLORS.open }}></span> Open ({analytics.status_mix.open})
                          </span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: STATUS_COLORS.investigating }}></span> Investigating ({analytics.status_mix.investigating})
                          </span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: STATUS_COLORS.mitigated }}></span> Mitigated ({analytics.status_mix.mitigated})
                          </span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: STATUS_COLORS.resolved }}></span> Resolved ({analytics.status_mix.resolved})
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="analytics-grid" style={{ marginTop: '0rem' }}>
                    <div className="chart-card">
                      <h3 className="section-title">Noisy Alerting Services (Top 5)</h3>
                      <div className="chart-wrapper">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={analytics.noisy_services}>
                            <XAxis dataKey="service_name" stroke="var(--text-muted)" fontSize={11} />
                            <YAxis stroke="var(--text-muted)" fontSize={11} />
                            <Tooltip 
                              contentStyle={{ 
                                backgroundColor: 'var(--bg-surface)', 
                                borderColor: 'var(--border-color)',
                                color: 'var(--text-primary)'
                              }} 
                            />
                            <Bar dataKey="alert_count" name="Total Alerts Ingested" fill="var(--color-info)" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="incident_count" name="Outages Triggered" fill="var(--accent-color)" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="chart-card">
                      <h3 className="section-title">Noisy Service Index Details</h3>
                      <div className="noisy-services-list">
                        {analytics.noisy_services.map((item, idx) => (
                          <div key={idx} className="noisy-service-item">
                            <span className="noisy-service-name">{item.service_name}</span>
                            <div className="noisy-service-stats">
                              <span>Alerts: <strong>{item.alert_count}</strong></span>
                              <span>Incidents: <strong>{item.incident_count}</strong></span>
                              <span>MTTR: <strong>{item.mttr_minutes}m</strong></span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </>
          )}

          {/* Ingestion Upload View */}
          {activeTab === 'upload' && (
            <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <div className="chart-card">
                <h3 className="section-title">Ingest Alert Logs</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                  Upload monitoring logs in CSV or JSON format. The ingestion pipeline parses payloads, normalizes columns, computes Jaccard-similar alerts to group duplicate incidents, and applies ML severity/root-cause classifiers.
                </p>

                <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                  <a 
                    href="/api/demo/template" 
                    className="btn btn-secondary"
                    style={{ fontSize: '0.85rem', padding: '0.5rem 1rem', textDecoration: 'none' }}
                  >
                    Download Template
                  </a>
                  <a 
                    href="/api/demo/sample-outage" 
                    className="btn btn-primary"
                    style={{ fontSize: '0.85rem', padding: '0.5rem 1rem', textDecoration: 'none' }}
                  >
                    Download Sample Outage File
                  </a>
                </div>

                <input 
                  type="file" 
                  ref={fileInputRef} 
                  style={{ display: 'none' }} 
                  accept=".csv,.json" 
                  onChange={handleFileUpload}
                />

                <div className="upload-area" onClick={triggerFileSelect}>
                  <Upload className="upload-icon" />
                  <div className="upload-text">
                    {uploading ? 'Processing files...' : <span>Click to select file</span>}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Supported schemas: JSON Array of alerts, or CSV headers: (timestamp, service_name, message, severity, host)
                  </div>
                </div>
              </div>

              {/* Upload Jobs Logs */}
              <div className="chart-card">
                <h3 className="section-title">Alert Ingest Jobs History</h3>
                {uploadJobs.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    No file uploads performed in this session.
                  </div>
                ) : (
                  <div className="job-list">
                    {uploadJobs.map((job) => (
                      <div key={job.id} className="job-card">
                        <div className="job-card-info">
                          <span className="job-filename">{job.filename}</span>
                          <span className="job-meta">
                            Job ID: {job.id.substring(0, 8)} • Ingested at {new Date(job.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                          {job.status === 'processing' && (
                            <span style={{ fontSize: '0.85rem', color: 'var(--color-warning)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <Clock size={14} className="loading-shimmer" /> Processing Queue...
                            </span>
                          )}
                          {job.status === 'completed' && (
                            <span style={{ fontSize: '0.85rem', color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                              <CheckCircle size={14} /> Ingested {job.alerts_count} alerts
                            </span>
                          )}
                          {job.status === 'failed' && (
                            <span style={{ fontSize: '0.85rem', color: 'var(--color-error)', display: 'flex', alignItems: 'center', gap: '0.25rem' }} title={job.error_message || ''}>
                              <X size={14} /> Failed ingestion
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Incident Details Right Panel Drawer */}
      {selectedIncidentId && (
        <div className="detail-overlay" onClick={() => setSelectedIncidentId(null)}>
          <div className="detail-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="detail-header">
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  <span>INCIDENT ID: #{selectedIncidentId}</span>
                  <span>•</span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>{selectedIncident?.service.name}</span>
                </div>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 600 }}>{selectedIncident?.title}</h3>
              </div>
              <button className="detail-close-btn" onClick={() => setSelectedIncidentId(null)}>
                <X size={20} />
              </button>
            </div>

            {loadingDetail || !selectedIncident ? (
              <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div className="loading-skeleton" style={{ width: '80%' }}></div>
                <div className="loading-skeleton" style={{ width: '100%', height: '100px' }}></div>
                <div className="loading-skeleton" style={{ width: '90%' }}></div>
              </div>
            ) : (
              <div className="detail-body">
                {/* Meta Controls (Interactive changes) */}
                <div className="detail-meta-grid">
                  <div className="detail-meta-item">
                    <span className="detail-meta-label">Current Status</span>
                    <select 
                      className="select-filter" 
                      style={{ marginTop: '0.25rem', backgroundColor: 'var(--bg-surface)' }}
                      value={selectedIncident.status}
                      onChange={(e) => handleUpdateStatus(e.target.value)}
                    >
                      <option value="open">Open</option>
                      <option value="investigating">Investigating</option>
                      <option value="mitigated">Mitigated</option>
                      <option value="resolved">Resolved</option>
                    </select>
                  </div>
                  
                  <div className="detail-meta-item">
                    <span className="detail-meta-label">Severity</span>
                    <select 
                      className="select-filter" 
                      style={{ marginTop: '0.25rem', backgroundColor: 'var(--bg-surface)' }}
                      value={selectedIncident.severity}
                      onChange={(e) => handleUpdateSeverity(e.target.value)}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>

                  <div className="detail-meta-item">
                    <span className="detail-meta-label">SLA Risk Category</span>
                    <select 
                      className="select-filter" 
                      style={{ marginTop: '0.25rem', backgroundColor: 'var(--bg-surface)' }}
                      value={selectedIncident.sla_risk}
                      onChange={(e) => handleUpdateSlaRisk(e.target.value)}
                    >
                      <option value="healthy">Healthy</option>
                      <option value="watch">Watch</option>
                      <option value="at-risk">At Risk</option>
                      <option value="breach-likely">Breach Likely</option>
                    </select>
                  </div>

                  <div className="detail-meta-item">
                    <span className="detail-meta-label">SLA Budget</span>
                    <span className="detail-meta-value" style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
                      {selectedIncident.service.sla_minutes} min (Tier {selectedIncident.service.criticality.replace('tier-', '')})
                    </span>
                  </div>
                </div>

                {/* ML Intelligence Panel */}
                <div className="ml-insights-panel">
                  <div className="ml-insights-header">
                    <Database size={16} />
                    <span>ML-Assisted Diagnostics Engine</span>
                  </div>
                  <div className="ml-insights-body">
                    <div className="ml-insight-card">
                      <span className="ml-insight-label">Predicted Severity</span>
                      <span className={`badge badge-sev-${(selectedIncident.predicted_severity || 'medium').toLowerCase()}`} style={{ width: 'fit-content', marginTop: '0.25rem' }}>
                        {selectedIncident.predicted_severity || 'MEDIUM'}
                      </span>
                    </div>
                    <div className="ml-insight-card">
                      <span className="ml-insight-label">Probable Root Cause Category</span>
                      <span className="ml-insight-value" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem' }}>
                        <Terminal size={14} style={{ color: 'var(--accent-color)' }} />
                        {selectedIncident.predicted_root_cause ? selectedIncident.predicted_root_cause.toUpperCase() : 'UNKNOWN'}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Recommendation Panel */}
                <div className="ml-insights-panel" style={{ marginTop: '1rem' }}>
                  <div className="ml-insights-header" style={{ backgroundColor: 'rgba(59, 130, 246, 0.05)', color: 'var(--color-info)' }}>
                    <Server size={16} />
                    <span>Recommended Remediation Actions</span>
                  </div>
                  <div style={{ padding: '1.25rem' }}>
                    {selectedIncident.predicted_root_cause && RECOMMENDATION_MAP[selectedIncident.predicted_root_cause.toLowerCase()] ? (
                      <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', listStyle: 'none' }}>
                        {RECOMMENDATION_MAP[selectedIncident.predicted_root_cause.toLowerCase()].map((rec, idx) => (
                          <li key={idx} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            <ChevronRight size={14} style={{ color: 'var(--accent-color)', flexShrink: 0, marginTop: '2px' }} />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                        No specific recommendations available for this root cause.
                      </div>
                    )}
                  </div>
                </div>

                {/* Alert cluster section */}
                <div>
                  <h4 className="section-title">Grouped Alerts Cluster ({selectedIncident.alerts.length})</h4>
                  <div className="alert-list">
                    {selectedIncident.alerts.map((alert) => (
                      <div key={alert.id} className="alert-card">
                        <div className="alert-card-header">
                          <span>Host: {alert.host || 'N/A'}</span>
                          <span>{formatDate(alert.timestamp)}</span>
                        </div>
                        <span className="alert-card-message">{alert.message}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Audit Timeline & Notes split */}
                <div className="timeline-notes-container">
                  <div>
                    <h4 className="section-title">Timeline Audit trail</h4>
                    <div className="timeline-flow">
                      {selectedIncident.timeline.map((event) => (
                        <div key={event.id} className={`timeline-item ${event.event_type}`}>
                          <span className="timeline-time">{formatDate(event.timestamp)}</span>
                          <div className="timeline-message">
                            <span className="timeline-operator">{event.operator_name}</span>: {event.message}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="notes-panel">
                    <h4 className="section-title">Operator Comments</h4>
                    
                    <form onSubmit={handleSubmitNote} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <textarea
                        className="notes-textarea"
                        placeholder="Attach diagnostic comment..."
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        required
                      ></textarea>
                      <button 
                        type="submit" 
                        className="btn btn-primary" 
                        style={{ alignSelf: 'flex-end', padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                        disabled={submittingNote}
                      >
                        {submittingNote ? 'Adding...' : 'Attach Comment'}
                      </button>
                    </form>

                    <div className="notes-list">
                      {selectedIncident.notes.length === 0 ? (
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>
                          No comments posted yet.
                        </div>
                      ) : (
                        selectedIncident.notes.map((note) => (
                          <div key={note.id} className="note-bubble">
                            <div className="note-bubble-header">
                              <span className="note-author">{note.operator_name}</span>
                              <span className="note-time">{new Date(note.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                            </div>
                            <p className="note-text">{note.content}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Toast Notification popup */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '2rem',
          right: '2rem',
          backgroundColor: toast.type === 'success' ? 'var(--color-success-bg)' : 'var(--color-error-bg)',
          color: toast.type === 'success' ? 'var(--color-success)' : 'var(--color-error)',
          border: `1px solid ${toast.type === 'success' ? 'var(--color-success)' : 'var(--color-error)'}`,
          padding: '0.75rem 1.5rem',
          borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-lg)',
          zIndex: 9999,
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontWeight: 500,
          animation: 'slide-in 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
        }}>
          {toast.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {toast.message}
        </div>
      )}
    </div>
  );
}
