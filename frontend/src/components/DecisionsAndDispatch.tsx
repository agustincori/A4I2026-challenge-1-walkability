import React, { useState } from 'react';
import { 
  Zap, 
  Truck, 
  ShieldCheck, 
  Users, 
  MapPin, 
  CheckCircle2, 
  FileText, 
  Clock,
  ArrowRight
} from 'lucide-react';
import { PlannerDecision, DispatchedAsset, AssetType, CensusTract } from '../types';

interface DecisionsAndDispatchProps {
  decisions: PlannerDecision[];
  dispatchedAssets: DispatchedAsset[];
  onExecuteDecision: (decision: PlannerDecision) => void;
  onDeployAsset: (type: AssetType, locationName: string, lat: number, lng: number, tractId?: string) => void;
  onRecallAsset: (id: string) => void;
  onSelectTractForMap: (tractId: string) => void;
  onDraftCouncilProposal: () => void;
  allTracts: CensusTract[];
}

export const DecisionsAndDispatch: React.FC<DecisionsAndDispatchProps> = ({
  decisions,
  dispatchedAssets,
  onExecuteDecision,
  onDeployAsset,
  onRecallAsset,
  onSelectTractForMap,
  onDraftCouncilProposal,
  allTracts,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'decisions' | 'resources'>('decisions');

  // Custom dispatch modal/form
  const [showCustomDeploy, setShowCustomDeploy] = useState(false);
  const [selectedAssetType, setSelectedAssetType] = useState<AssetType>('hydration');
  const [targetTractGeoId, setTargetTractGeoId] = useState<string>(allTracts[0]?.geoId || '13121006802');

  // Calculate live impact metrics
  const totalProtectedPopulation = dispatchedAssets.reduce((sum, a) => sum + a.protectedPopulation, 0) + 4250;
  const equityTargetRatePct = 88.4;

  // Counts of available inventory (base minus deployed)
  const deployedCounts = {
    hydration: dispatchedAssets.filter((a) => a.type === 'hydration').length,
    wellness: dispatchedAssets.filter((a) => a.type === 'wellness').length,
    bus: dispatchedAssets.filter((a) => a.type === 'bus').length,
  };

  const inventory = [
    {
      type: 'hydration' as AssetType,
      name: 'Potable Hydration Trailer',
      description: '1,000-gal chilled potable water reservoir + electrolyte misting fans',
      total: 5,
      available: Math.max(0, 5 - deployedCounts.hydration),
      icon: '💧',
      color: 'amber',
    },
    {
      type: 'wellness' as AssetType,
      name: 'Mobile Wellness Van',
      description: 'Paramedic triage team + cooling ice vests + hydration assessment',
      total: 4,
      available: Math.max(0, 4 - deployedCounts.wellness),
      icon: '🚑',
      color: 'indigo',
    },
    {
      type: 'bus' as AssetType,
      name: 'MARTA Climate Shelter Bus',
      description: 'Dedicated air-conditioned 68°F shelter bus staged at transit desert stops',
      total: 4,
      available: Math.max(0, 4 - deployedCounts.bus),
      icon: '🚌',
      color: 'cyan',
    },
  ];

  const handleCustomDispatchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const tract = allTracts.find((t) => t.geoId === targetTractGeoId);
    if (!tract) return;
    onDeployAsset(
      selectedAssetType,
      `${tract.neighborhood} (${tract.name})`,
      tract.latitude,
      tract.longitude,
      tract.geoId
    );
    setShowCustomDeploy(false);
  };

  const pendingDecisionsCount = decisions.filter((d) => d.status === 'pending').length;

  return (
    <div className="space-y-6">
      {/* Header & Sub-tab Switcher */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <Zap className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Planner Action Deck: Decisions & Resource Mover
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Triage immediate municipal heat actions and deploy mobile cooling assets directly into verified thermal hotspots.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveSubTab('decisions')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeSubTab === 'decisions'
                  ? 'bg-rose-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <span>⚡ Decisions Needed</span>
              {pendingDecisionsCount > 0 && (
                <span className="bg-rose-500 text-white text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                  {pendingDecisionsCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveSubTab('resources')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                activeSubTab === 'resources'
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <span>🚛 Resource Mover</span>
              <span className="bg-indigo-500/20 text-indigo-300 text-[10px] px-1.5 py-0.2 rounded border border-indigo-500/30 font-mono">
                {dispatchedAssets.length} Active
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Real-Time Impact Counters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">Protected Population</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-extrabold text-emerald-400 mt-1 font-mono">
            {totalProtectedPopulation.toLocaleString()}
          </p>
          <span className="text-[11px] text-emerald-300/80 mt-0.5 block">
            +{(dispatchedAssets.length * 2100).toLocaleString()} residents covered via mobile dispatches
          </span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">Equity Target Rate</span>
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-extrabold text-indigo-400 mt-1 font-mono">{equityTargetRatePct}%</p>
          <span className="text-[11px] text-indigo-300/80 mt-0.5 block">
            Exceeds City of Atlanta 75th percentile vulnerability criteria
          </span>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">City Council Memo</span>
            <FileText className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={onDraftCouncilProposal}
              className="flex-1 bg-gradient-to-r from-rose-600 to-indigo-600 hover:from-rose-500 hover:to-indigo-500 text-white text-xs font-semibold py-2 px-3 rounded-lg transition flex items-center justify-center gap-1.5 shadow"
            >
              <span>Draft Council Memo</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* SUB-VIEW 1: DECISIONS NEEDED */}
      {activeSubTab === 'decisions' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <span>Immediate Municipal Triage Actions</span>
              <span className="text-xs font-normal text-slate-400 lowercase">({decisions.length} items logged)</span>
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {decisions.map((dec) => {
              const isExecuted = dec.status === 'executed';
              return (
                <div
                  key={dec.id}
                  className={`p-4 rounded-xl border transition-all ${
                    isExecuted
                      ? 'bg-slate-900/40 border-slate-800 opacity-75'
                      : 'bg-slate-900/90 border-slate-700/80 shadow-md hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                        dec.category === 'Immediate'
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                          : dec.category === 'Mobile Surge'
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                          : dec.category === 'Transit Desert'
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                          : 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30'
                      }`}
                    >
                      {dec.category}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {dec.dueTime}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold text-white mb-1">{dec.title}</h4>
                  <p className="text-xs text-slate-300 leading-relaxed mb-3">{dec.description}</p>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                    <span className="text-[11px] text-emerald-400 font-medium">
                      Protect: {dec.impactPopulation.toLocaleString()} residents
                    </span>

                    <div className="flex items-center gap-2">
                      {dec.tractId && (
                        <button
                          onClick={() => onSelectTractForMap(dec.tractId!)}
                          className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-2.5 py-1.5 rounded-lg transition"
                          title="View tract on tactical map"
                        >
                          Map
                        </button>
                      )}

                      {isExecuted ? (
                        <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-950/40 border border-emerald-800/40">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Executed
                        </span>
                      ) : (
                        <button
                          onClick={() => onExecuteDecision(dec)}
                          className="bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition shadow"
                        >
                          {dec.actionLabel}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SUB-VIEW 2: RESOURCE MOVER / DISPATCHER */}
      {activeSubTab === 'resources' && (
        <div className="space-y-6">
          {/* Inventory Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {inventory.map((item) => (
              <div
                key={item.type}
                className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl flex flex-col justify-between shadow-lg"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl">{item.icon}</span>
                    <span className="font-mono text-xs font-bold text-amber-300 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                      {item.available} / {item.total} Ready
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white">{item.name}</h4>
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{item.description}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 font-mono">Deployment time: ~15m</span>
                  <button
                    onClick={() => {
                      setSelectedAssetType(item.type);
                      setShowCustomDeploy(true);
                    }}
                    disabled={item.available <= 0}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition"
                  >
                    Deploy Unit
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Active Mobile Field Units List */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Truck className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">Active Mobile Dispatches ({dispatchedAssets.length})</h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">Live telemetry linked to Tactical Map</span>
            </div>

            {dispatchedAssets.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-6">
                No mobile units currently deployed. Use the inventory above or Decisions Needed to dispatch units.
              </p>
            ) : (
              <div className="space-y-2.5">
                {dispatchedAssets.map((asset) => (
                  <div
                    key={asset.id}
                    className="bg-slate-950/70 p-3 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xl">
                        {asset.type === 'hydration' ? '💧' : asset.type === 'wellness' ? '🚑' : '🚌'}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-white">{asset.name}</span>
                          <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            {asset.status === 'on-site' ? 'On Site' : 'En Route'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-500" />
                          <span>{asset.locationName}</span>
                          <span className="text-slate-600">•</span>
                          <span className="text-emerald-400">+{asset.protectedPopulation.toLocaleString()} residents</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {asset.tractId && (
                        <button
                          onClick={() => onSelectTractForMap(asset.tractId!)}
                          className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-2.5 py-1.5 rounded-lg transition"
                        >
                          Focus on Map
                        </button>
                      )}
                      <button
                        onClick={() => onRecallAsset(asset.id)}
                        className="bg-slate-800 hover:bg-rose-900/40 text-slate-400 hover:text-rose-300 text-xs px-2.5 py-1.5 rounded-lg transition"
                        title="Recall mobile asset back to base"
                      >
                        Recall
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Custom Dispatch Modal */}
      {showCustomDeploy && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="font-bold text-white text-base mb-1">Dispatch Mobile Climate Asset</h3>
            <p className="text-xs text-slate-400 mb-4">
              Direct mobile resilience infrastructure into high thermal offset census tracts.
            </p>

            <form onSubmit={handleCustomDispatchSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Asset Type</label>
                <select
                  value={selectedAssetType}
                  onChange={(e) => setSelectedAssetType(e.target.value as AssetType)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="hydration">💧 Hydration Station Trailer (1,000 gal)</option>
                  <option value="wellness">🚑 Mobile Wellness Van (Paramedic Triage)</option>
                  <option value="bus">🚌 MARTA Cooling Bus (68°F Shelter)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Destination Target Tract</label>
                <select
                  value={targetTractGeoId}
                  onChange={(e) => setTargetTractGeoId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  {allTracts.map((tract) => (
                    <option key={tract.geoId} value={tract.geoId}>
                      {tract.neighborhood} (Offset: +{tract.predictedOffsetF}°F | Poverty: {tract.povertyRatePct}%)
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCustomDeploy(false)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded-xl text-xs font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-semibold transition shadow"
                >
                  Confirm Dispatch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
