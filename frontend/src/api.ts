import {
  HealthData,
  RunSummary,
  RunDetail,
  ValidationSummary,
  CampaignItem,
  AttributionComparisonData,
  CustomerJourneyData,
  DataIssueItem,
  MetricsData,
  ExportItem,
} from './types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthData> {
  const res = await fetch('/health');
  if (!res.ok) throw new Error('Failed to fetch health');
  return res.json();
}

export async function fetchRuns(): Promise<RunSummary[]> {
  const res = await fetch(`${API_BASE}/runs`);
  if (!res.ok) throw new Error('Failed to fetch runs');
  return res.json();
}

export async function fetchRunDetail(runId: string): Promise<RunDetail> {
  const res = await fetch(`${API_BASE}/runs/${runId}`);
  if (!res.ok) throw new Error(`Failed to fetch run ${runId}`);
  return res.json();
}

export async function fetchValidationSummary(runId: string): Promise<ValidationSummary> {
  const res = await fetch(`${API_BASE}/runs/${runId}/validation`);
  if (!res.ok) throw new Error(`Failed to fetch validation for ${runId}`);
  return res.json();
}

export async function fetchCampaigns(search?: string, channelId?: string): Promise<{ total: number; campaigns: CampaignItem[] }> {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (channelId) params.set('channel_id', channelId);
  params.set('page_size', '50');

  const res = await fetch(`${API_BASE}/campaigns?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch campaigns');
  return res.json();
}

export async function fetchAttributionComparison(startDate?: string, endDate?: string): Promise<AttributionComparisonData> {
  const params = new URLSearchParams();
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);

  const res = await fetch(`${API_BASE}/attribution/compare?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch attribution comparison');
  return res.json();
}

export async function fetchCustomerJourney(contactId: string): Promise<CustomerJourneyData> {
  const res = await fetch(`${API_BASE}/contacts/${contactId}/journey`);
  if (!res.ok) throw new Error(`Failed to fetch journey for contact ${contactId}`);
  return res.json();
}

export async function fetchIssues(issueType?: string, severity?: string): Promise<{ total: number; issues: DataIssueItem[] }> {
  const params = new URLSearchParams();
  if (issueType) params.set('issue_type', issueType);
  if (severity) params.set('severity', severity);
  params.set('page_size', '50');

  const res = await fetch(`${API_BASE}/issues?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch issues');
  return res.json();
}

export async function fetchMetrics(): Promise<MetricsData> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch evaluation metrics');
  return res.json();
}

export async function fetchExports(runId: string): Promise<{ run_id: string; exports: ExportItem[] }> {
  const res = await fetch(`${API_BASE}/exports/${runId}`);
  if (!res.ok) throw new Error(`Failed to fetch exports for ${runId}`);
  return res.json();
}

