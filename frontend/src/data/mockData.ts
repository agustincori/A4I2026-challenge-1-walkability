import { CensusTract, CoolingCenterRanking, StationHeatRecord, FeatureAttribution, EquityAuditSummary } from '../types';

export const CITYWIDE_BENCHMARKS = {
  city: 'Atlanta, GA',
  totalPopulation: 498715,
  citywideMedianPovertyPct: 18.2,
  citywideP75PovertyPct: 24.5,
  citywideMedianNoVehiclePct: 10.4,
  citywideP75NoVehiclePct: 14.8,
  baselineAverageTempF: 92.0,
  citywideMedianAge: 33.6,
  citywideMedianIncome: 69164,
};

export const MOCK_CENSUS_TRACTS: CensusTract[] = [
  {
    geoId: '13121006802',
    name: 'Census Tract 68.02',
    neighborhood: 'South Pryor St / Peoplestown',
    latitude: 33.7298,
    longitude: -84.3942,
    totalPop: 3420,
    povertyRatePct: 38.4,
    noVehicleRatePct: 28.5,
    medianIncome: 28400,
    medianAge: 34.2,
    medianYearBuilt: 1958,
    housingUnits: 1420,
    predictedOffsetF: 4.2,
    treeCanopyPct: 14.2,
    walkScore: 68,
    hasCoolingCenter: true,
    coolingCenterName: 'South Pryor Community Center',
    coolingCenterType: 'Community Center'
  },
  {
    geoId: '13121007808',
    name: 'Census Tract 78.08',
    neighborhood: 'Bankhead / English Avenue / Vine City',
    latitude: 33.7654,
    longitude: -84.4215,
    totalPop: 2890,
    povertyRatePct: 42.1,
    noVehicleRatePct: 34.0,
    medianIncome: 24150,
    medianAge: 32.8,
    medianYearBuilt: 1962,
    housingUnits: 1310,
    predictedOffsetF: 3.8,
    treeCanopyPct: 16.5,
    walkScore: 71,
    hasCoolingCenter: true,
    coolingCenterName: 'English Avenue Resilience Hub',
    coolingCenterType: 'Recreation Center'
  },
  {
    geoId: '13121007603',
    name: 'Census Tract 76.03',
    neighborhood: 'West End / Campbellton Corridor',
    latitude: 33.7381,
    longitude: -84.4289,
    totalPop: 4120,
    povertyRatePct: 31.2,
    noVehicleRatePct: 22.1,
    medianIncome: 34800,
    medianAge: 36.5,
    medianYearBuilt: 1965,
    housingUnits: 1890,
    predictedOffsetF: 3.5,
    treeCanopyPct: 21.0,
    walkScore: 64,
    hasCoolingCenter: true,
    coolingCenterName: 'West End Regional Library',
    coolingCenterType: 'Library'
  },
  {
    geoId: '13121002200',
    name: 'Census Tract 22.00',
    neighborhood: 'Thomasville Heights / South Atlanta',
    latitude: 33.7085,
    longitude: -84.3721,
    totalPop: 2340,
    povertyRatePct: 44.5,
    noVehicleRatePct: 36.2,
    medianIncome: 21900,
    medianAge: 31.0,
    medianYearBuilt: 1970,
    housingUnits: 1120,
    predictedOffsetF: 4.6,
    treeCanopyPct: 15.0,
    walkScore: 48,
    hasCoolingCenter: true,
    coolingCenterName: 'Thomasville Recreation Center',
    coolingCenterType: 'Recreation Center'
  },
  {
    geoId: '13121001900',
    name: 'Census Tract 19.00',
    neighborhood: 'Pittsburgh / University Homes',
    latitude: 33.7312,
    longitude: -84.4075,
    totalPop: 2650,
    povertyRatePct: 41.0,
    noVehicleRatePct: 29.8,
    medianIncome: 26300,
    medianAge: 33.5,
    medianYearBuilt: 1954,
    housingUnits: 1250,
    predictedOffsetF: 3.9,
    treeCanopyPct: 18.2,
    walkScore: 60,
    hasCoolingCenter: false
  },
  {
    geoId: '13121006300',
    name: 'Census Tract 63.00',
    neighborhood: 'Sweet Auburn / Downtown Core',
    latitude: 33.7550,
    longitude: -84.3812,
    totalPop: 3780,
    povertyRatePct: 32.5,
    noVehicleRatePct: 38.1,
    medianIncome: 31500,
    medianAge: 29.8,
    medianYearBuilt: 1978,
    housingUnits: 2310,
    predictedOffsetF: 4.8,
    treeCanopyPct: 8.5,
    walkScore: 89,
    hasCoolingCenter: false
  },
  {
    geoId: '13121008301',
    name: 'Census Tract 83.01',
    neighborhood: 'Grove Park / Donald Lee Hollowell',
    latitude: 33.7745,
    longitude: -84.4480,
    totalPop: 3510,
    povertyRatePct: 29.8,
    noVehicleRatePct: 21.4,
    medianIncome: 35200,
    medianAge: 37.1,
    medianYearBuilt: 1968,
    housingUnits: 1620,
    predictedOffsetF: 2.9,
    treeCanopyPct: 26.4,
    walkScore: 52,
    hasCoolingCenter: false
  },
  {
    geoId: '13121004400',
    name: 'Census Tract 44.00',
    neighborhood: 'Old Fourth Ward / Inman Park',
    latitude: 33.7610,
    longitude: -84.3645,
    totalPop: 5120,
    povertyRatePct: 12.5,
    noVehicleRatePct: 11.2,
    medianIncome: 78500,
    medianAge: 34.0,
    medianYearBuilt: 1995,
    housingUnits: 3400,
    predictedOffsetF: 0.8,
    treeCanopyPct: 32.0,
    walkScore: 82,
    hasCoolingCenter: false
  },
  {
    geoId: '13121003500',
    name: 'Census Tract 35.00',
    neighborhood: 'East Atlanta Village / Kirkwood',
    latitude: 33.7410,
    longitude: -84.3410,
    totalPop: 4210,
    povertyRatePct: 14.1,
    noVehicleRatePct: 8.9,
    medianIncome: 74200,
    medianAge: 35.8,
    medianYearBuilt: 1982,
    housingUnits: 2150,
    predictedOffsetF: 0.4,
    treeCanopyPct: 38.5,
    walkScore: 65,
    hasCoolingCenter: false
  },
  {
    geoId: '13121005800',
    name: 'Census Tract 58.00',
    neighborhood: 'Piedmont Park / Midtown East',
    latitude: 33.7850,
    longitude: -84.3735,
    totalPop: 6200,
    povertyRatePct: 6.2,
    noVehicleRatePct: 4.5,
    medianIncome: 112000,
    medianAge: 33.2,
    medianYearBuilt: 2005,
    housingUnits: 4800,
    predictedOffsetF: -2.1,
    treeCanopyPct: 54.0,
    walkScore: 88,
    hasCoolingCenter: false
  },
  {
    geoId: '13121009100',
    name: 'Census Tract 91.00',
    neighborhood: 'Buckhead / Peachtree Heights',
    latitude: 33.8240,
    longitude: -84.3850,
    totalPop: 5400,
    povertyRatePct: 4.8,
    noVehicleRatePct: 3.2,
    medianIncome: 148000,
    medianAge: 39.4,
    medianYearBuilt: 1998,
    housingUnits: 3900,
    predictedOffsetF: -2.8,
    treeCanopyPct: 58.2,
    walkScore: 59,
    hasCoolingCenter: false
  }
];

export const MOCK_COOLING_CENTER_RANKINGS: CoolingCenterRanking[] = [
  {
    rank: 1,
    tractId: '13121006802',
    neighborhood: 'South Pryor St / Peoplestown',
    name: 'South Pryor Community Center',
    latitude: 33.7298,
    longitude: -84.3942,
    predictedOffsetF: 4.2,
    population: 3420,
    povertyRatePct: 38.4,
    noVehicleRatePct: 28.5,
    compositeScore: 3.69,
    sitingJustification: 'Highest composite risk: runs +4.2°F hotter than city baseline combined with 38.4% poverty and 28.5% transit dependency.',
    walkAccessMinutes: 8
  },
  {
    rank: 2,
    tractId: '13121007808',
    neighborhood: 'Bankhead / English Avenue',
    name: 'English Avenue Resilience Hub',
    latitude: 33.7654,
    longitude: -84.4215,
    predictedOffsetF: 3.8,
    population: 2890,
    povertyRatePct: 42.1,
    noVehicleRatePct: 34.0,
    compositeScore: 3.80,
    sitingJustification: 'Acute social vulnerability: 42.1% poverty and 34.0% carless households with +3.8°F microclimate heat offset.',
    walkAccessMinutes: 10
  },
  {
    rank: 3,
    tractId: '13121002200',
    neighborhood: 'Thomasville Heights / South Atlanta',
    name: 'Thomasville Community Recreation Facility',
    latitude: 33.7085,
    longitude: -84.3721,
    predictedOffsetF: 4.6,
    population: 2340,
    povertyRatePct: 44.5,
    noVehicleRatePct: 36.2,
    compositeScore: 4.26,
    sitingJustification: 'Severe heat island anomaly (+4.6°F) and extreme economic isolation (44.5% poverty, 36.2% vehicle deficit).',
    walkAccessMinutes: 12
  },
  {
    rank: 4,
    tractId: '13121007603',
    neighborhood: 'West End / Campbellton Corridor',
    name: 'West End Regional Library',
    latitude: 33.7381,
    longitude: -84.4289,
    predictedOffsetF: 3.5,
    population: 4120,
    povertyRatePct: 31.2,
    noVehicleRatePct: 22.1,
    compositeScore: 3.00,
    sitingJustification: 'Strategic high-density transit node serving over 4,100 residents at elevated thermal risk.',
    walkAccessMinutes: 6
  },
  {
    rank: 5,
    tractId: '13121001900',
    neighborhood: 'Pittsburgh / University Homes',
    name: 'Pittsburgh Community Siting Hub',
    latitude: 33.7312,
    longitude: -84.4075,
    predictedOffsetF: 3.9,
    population: 2650,
    povertyRatePct: 41.0,
    noVehicleRatePct: 29.8,
    compositeScore: 3.68,
    sitingJustification: 'Unbuffered historic housing with +3.9°F offset, requiring emergency indoor cooling backup.',
    walkAccessMinutes: 9
  }
];

export const MOCK_STATION_HEAT_HISTORY: StationHeatRecord[] = [
  {
    year: 2018,
    daysExceeding90F: 62,
    daysExceeding95F: 9,
    daysExceeding100F: 0,
    peakTempF: 97.2,
    avgSummerMaxF: 89.4
  },
  {
    year: 2019,
    daysExceeding90F: 91,
    daysExceeding95F: 23,
    daysExceeding100F: 0,
    peakTempF: 99.1,
    avgSummerMaxF: 92.1
  },
  {
    year: 2020,
    daysExceeding90F: 55,
    daysExceeding95F: 8,
    daysExceeding100F: 0,
    peakTempF: 96.0,
    avgSummerMaxF: 88.7
  },
  {
    year: 2021,
    daysExceeding90F: 48,
    daysExceeding95F: 6,
    daysExceeding100F: 0,
    peakTempF: 95.3,
    avgSummerMaxF: 88.1
  },
  {
    year: 2022,
    daysExceeding90F: 74,
    daysExceeding95F: 18,
    daysExceeding100F: 0,
    peakTempF: 98.4,
    avgSummerMaxF: 90.8
  },
  {
    year: 2023,
    daysExceeding90F: 82,
    daysExceeding95F: 21,
    daysExceeding100F: 1,
    peakTempF: 100.2,
    avgSummerMaxF: 91.5
  },
  {
    year: 2024,
    daysExceeding90F: 86,
    daysExceeding95F: 25,
    daysExceeding100F: 2,
    peakTempF: 101.4,
    avgSummerMaxF: 92.6
  }
];

export const MOCK_FEATURE_ATTRIBUTIONS: FeatureAttribution[] = [
  {
    feature: 'Lack of Tree Canopy / Pavement Fraction',
    attributionF: 1.85,
    baselineContribution: '+1.85°F thermal amplification from asphalt & unshaded roadways',
    impactDirection: 'increases_heat'
  },
  {
    feature: 'Building Vintage & Thermal Mass (pre-1970 construction)',
    attributionF: 1.25,
    baselineContribution: '+1.25°F retained heat from older masonry & low-insulation roofscapes',
    impactDirection: 'increases_heat'
  },
  {
    feature: 'Socioeconomic Disinvestment & Impervious Density',
    attributionF: 0.85,
    baselineContribution: '+0.85°F from high building density and missing vegetative buffers',
    impactDirection: 'increases_heat'
  },
  {
    feature: 'Elevation & Macro Topography',
    attributionF: 0.25,
    baselineContribution: '+0.25°F basin microclimate effect',
    impactDirection: 'increases_heat'
  }
];

export const MOCK_EQUITY_AUDIT: EquityAuditSummary = {
  citywidePovertyP75: CITYWIDE_BENCHMARKS.citywideP75PovertyPct,
  citywideNoVehicleP75: CITYWIDE_BENCHMARKS.citywideP75NoVehiclePct,
  recommendedTractsCount: 3,
  povertyAuditPass: true,
  transitAuditPass: true,
  overallAuditPass: true,
  averagePovertyPct: 41.67,
  averageNoVehiclePct: 32.90,
  justificationNotes:
    '100% of top-3 recommended cooling center tracts exceed the Atlanta 75th percentile for poverty (24.5%) and no-vehicle rate (14.8%). The intervention rigorously counteracts historic environmental disparities by directing resources to highest-need neighborhoods.'
};
