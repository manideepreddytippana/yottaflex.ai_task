export interface HealthData {
  status: string;
  version: string;
  database_connected: boolean;
  timestamp: string;
}

export interface RunSummary {
  run_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  seed: number;
  generator_version: string;
  dataset_scale: string;
  total_entities: number;
}

export interface RunDetail {
  run_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  seed: number;
  generator_version: string;
  config_hash: string;
  dataset_scale: string;
  row_counts: Record<string, number>;
  checksums: Record<string, string>;
}

export interface ValidationSummary {
  run_id: string;
  overall_status: string;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  checks: Array<{
    check_name: string;
    entity_name: string;
    records_checked: number;
    failure_count: number;
    status: string;
    details?: any;
  }>;
}

export interface CampaignItem {
  campaign_id: string;
  name: string;
  channel_id: string;
  channel_name?: string;
  status: string;
  budget_amount: number;
  actual_spend: number;
  spend_coverage_status: string;
  attributed_revenue_linear: number;
  roi_percent_linear?: number;
  start_at: string;
  end_at: string;
}

export interface AttributionModelSummary {
  model: string;
  attributed_revenue: number;
  total_orders_attributed: number;
  reconciliation_status: string;
  overall_roi_percent?: number;
}

export interface CampaignComparison {
  campaign_id: string;
  campaign_name: string;
  channel_name: string;
  actual_spend: number;
  first_touch_revenue: number;
  first_touch_roi?: number;
  last_touch_revenue: number;
  last_touch_roi?: number;
  linear_revenue: number;
  linear_roi?: number;
}

export interface AttributionComparisonData {
  reporting_currency: string;
  period: { start?: string; end?: string };
  total_eligible_revenue: number;
  unattributed_revenue: number;
  models: AttributionModelSummary[];
  campaign_comparison: CampaignComparison[];
}

export interface JourneyTimelineItem {
  event_id: string;
  event_type: string;
  occurred_at: string;
  title: string;
  details: Record<string, any>;
  is_eligible_touch?: boolean;
  exclusion_reason?: string;
}

export interface CustomerJourneyData {
  contact_id: string;
  full_name: string;
  email: string;
  lifecycle_stage: string;
  total_touchpoints: number;
  total_orders: number;
  total_spend_attributed: number;
  timeline: JourneyTimelineItem[];
}

export interface DataIssueItem {
  issue_id: string;
  entity_type: string;
  entity_id: string;
  issue_type: string;
  severity: string;
  detected_at: string;
  decision?: string;
  resolution_status: string;
}

export interface MetricsData {
  precision: number;
  recall: number;
  f1_score: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  attribution_coverage_percent: number;
  roi_availability_percent: number;
  reconciliation_pass_rate_percent: number;
  scenarios_evaluated: string[];
}

export interface ExportItem {
  filename: string;
  file_type: string;
  file_size_bytes: number;
  checksum_sha256?: string;
  relative_path: string;
}

