export interface CensusTract {
  geoId: string;
  name: string;
  neighborhood: string;
  latitude: number;
  longitude: number;
  totalPop: number;
  povertyRatePct: number;
  noVehicleRatePct: number;
  medianIncome: number;
  medianAge: number;
  medianYearBuilt: number;
  housingUnits: number;
  predictedOffsetF: number;
  treeCanopyPct: number;
  walkScore: number;
  sviScore?: number;
  integratedRiskScore?: number;
  hasCoolingCenter?: boolean;
  coolingCenterName?: string;
  coolingCenterType?: 'Library' | 'Recreation Center' | 'Community Center' | 'High School';
}

export interface CoolingCenterRanking {
  rank: number;
  tractId: string;
  neighborhood: string;
  name: string;
  latitude: number;
  longitude: number;
  predictedOffsetF: number;
  localizedTempF?: number;
  population: number;
  povertyRatePct: number;
  noVehicleRatePct: number;
  compositeScore: number;
  sitingJustification: string;
  walkAccessMinutes: number;
}

export interface StationHeatRecord {
  year: number;
  daysExceeding90F: number;
  daysExceeding95F: number;
  daysExceeding100F: number;
  peakTempF: number;
  avgSummerMaxF: number;
}

export interface FeatureAttribution {
  feature: string;
  attributionF: number;
  baselineContribution: string;
  impactDirection: 'increases_heat' | 'reduces_heat';
}

export interface EquityAuditSummary {
  citywidePovertyP75: number;
  citywideNoVehicleP75: number;
  recommendedTractsCount: number;
  povertyAuditPass: boolean;
  transitAuditPass: boolean;
  overallAuditPass: boolean;
  averagePovertyPct: number;
  averageNoVehiclePct: number;
  justificationNotes: string;
}

export interface ToolCallTrace {
  name: string;
  arguments: Record<string, any>;
  output?: Record<string, any> | string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  toolCalls?: ToolCallTrace[];
  model?: string;
  latencyMs?: number;
}

export type AssetType = 'hydration' | 'wellness' | 'bus';

export interface DispatchedAsset {
  id: string;
  type: AssetType;
  name: string;
  locationName: string;
  lat: number;
  lng: number;
  tractId?: string;
  dispatchedAt: string;
  status: 'en-route' | 'on-site';
  protectedPopulation: number;
}

export interface PlannerDecision {
  id: string;
  title: string;
  description: string;
  category: 'Immediate' | 'Mobile Surge' | 'Vulnerability' | 'Transit Desert';
  dueTime: string;
  actionLabel: string;
  actionType: 'draft_council' | 'deploy_hydration' | 'deploy_wellness' | 'stage_bus';
  tractId?: string;
  locationName?: string;
  lat?: number;
  lng?: number;
  impactPopulation: number;
  status: 'pending' | 'executed';
}

export interface HeatAlert {
  id: string;
  title: string;
  zone: string;
  severity: 'warning' | 'advisory' | 'spike';
  description: string;
  recommendation: string;
}

