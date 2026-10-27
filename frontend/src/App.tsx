import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { HeatMap } from './components/HeatMap';
import { CoolingCenterRankings } from './components/CoolingCenterRankings';
import { EquityAuditDashboard } from './components/EquityAuditDashboard';
import { HistoricalTrends } from './components/HistoricalTrends';
import { AdvisorChat } from './components/AdvisorChat';
import { ExplainabilityModal } from './components/ExplainabilityModal';
import { MOCK_CENSUS_TRACTS, MOCK_COOLING_CENTER_RANKINGS } from './data/mockData';
import { CensusTract, CoolingCenterRanking } from './types';
import { agentApi, CLOUD_RUN_URL } from './services/agentApi';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('map');
  const [isCloudRunConnected, setIsCloudRunConnected] = useState<boolean>(false);
  const [latencyMs, setLatencyMs] = useState<number>(0);
  const [useMockMode, setUseMockMode] = useState<boolean>(false);
  const [forecastBaselineF, setForecastBaselineF] = useState<number>(92);

  const [selectedTract, setSelectedTract] = useState<CensusTract | null>(MOCK_CENSUS_TRACTS[0]);
  const [explainTract, setExplainTract] = useState<CensusTract | null>(null);
  const [advisorPrompt, setAdvisorPrompt] = useState<string | undefined>(undefined);

  // Ping health of deployed Cloud Run service
  const verifyAgentHealth = async () => {
    const res = await agentApi.checkHealth();
    setIsCloudRunConnected(res.ok);
    setLatencyMs(res.latencyMs);
  };

  useEffect(() => {
    verifyAgentHealth();
    const timer = setInterval(verifyAgentHealth, 30000); // Check every 30s
    return () => clearInterval(timer);
  }, []);

  const handleAskAgentAboutTract = (tract: CensusTract) => {
    const prompt = `Provide a microclimate vulnerability assessment for ${tract.neighborhood} (Census Tract ${tract.geoId}). Why does it run ${tract.predictedOffsetF > 0 ? '+' : ''}${tract.predictedOffsetF}°F above baseline?`;
    setAdvisorPrompt(prompt);
    setActiveTab('advisor');
  };

  const handleSelectRanking = (rank: CoolingCenterRanking) => {
    const tract = MOCK_CENSUS_TRACTS.find((t) => t.geoId === rank.tractId);
    if (tract) {
      setSelectedTract(tract);
      setExplainTract(tract);
    }
  };

  const handleAuditRecommendations = (_selected: CoolingCenterRanking[]) => {
    setActiveTab('equity');
  };

  const handleDraftCouncilProposal = (selected: CoolingCenterRanking[]) => {
    const tractIds = selected.map((s) => s.tractId).join(', ');
    const prompt = `Draft a formal municipal council proposal for Atlanta City Council recommending cooling centers in tracts ${tractIds}. Include thermal offsets, poverty rates, and equity justification.`;
    setAdvisorPrompt(prompt);
    setActiveTab('advisor');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isCloudRunConnected={isCloudRunConnected}
        latencyMs={latencyMs}
        useMockMode={useMockMode}
        setUseMockMode={setUseMockMode}
        onRefreshHealth={verifyAgentHealth}
        cloudRunUrl={CLOUD_RUN_URL}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeTab === 'map' && (
          <HeatMap
            tracts={MOCK_CENSUS_TRACTS}
            selectedTract={selectedTract}
            onSelectTract={(t) => setSelectedTract(t)}
            onAskAgentAboutTract={handleAskAgentAboutTract}
            forecastBaselineF={forecastBaselineF}
          />
        )}

        {activeTab === 'siting' && (
          <CoolingCenterRankings
            rankings={MOCK_COOLING_CENTER_RANKINGS}
            forecastBaselineF={forecastBaselineF}
            setForecastBaselineF={setForecastBaselineF}
            onSelectRanking={handleSelectRanking}
            onAuditRecommendations={handleAuditRecommendations}
            onDraftCouncilProposal={handleDraftCouncilProposal}
          />
        )}

        {activeTab === 'equity' && (
          <EquityAuditDashboard recommendedSites={MOCK_COOLING_CENTER_RANKINGS.slice(0, 3)} />
        )}

        {activeTab === 'history' && <HistoricalTrends />}

        {activeTab === 'advisor' && (
          <AdvisorChat
            useMockMode={useMockMode}
            initialPrompt={advisorPrompt}
            onClearInitialPrompt={() => setAdvisorPrompt(undefined)}
          />
        )}
      </main>

      {/* Feature Attribution Explainability Modal */}
      <ExplainabilityModal
        isOpen={!!explainTract}
        onClose={() => setExplainTract(null)}
        tract={explainTract}
      />
    </div>
  );
};
export default App;
