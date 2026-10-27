import React, { useState } from 'react';
import { CoolingCenterRanking } from '../types';
import { Award, Thermometer, ShieldAlert, Footprints, FileText, CheckCircle2, ChevronRight, Sliders } from 'lucide-react';

interface CoolingCenterRankingsProps {
  rankings: CoolingCenterRanking[];
  forecastBaselineF: number;
  setForecastBaselineF: (temp: number) => void;
  onSelectRanking: (rank: CoolingCenterRanking) => void;
  onAuditRecommendations: (selectedRanks: CoolingCenterRanking[]) => void;
  onDraftCouncilProposal: (selectedRanks: CoolingCenterRanking[]) => void;
}

export const CoolingCenterRankings: React.FC<CoolingCenterRankingsProps> = ({
  rankings,
  forecastBaselineF,
  setForecastBaselineF,
  onSelectRanking,
  onAuditRecommendations,
  onDraftCouncilProposal,
}) => {
  const [fundingSlots, setFundingSlots] = useState<number>(3);
  const [showFormulaDetails, setShowFormulaDetails] = useState<boolean>(false);

  const selectedCandidates = rankings.slice(0, fundingSlots);

  return (
    <div className="space-y-6">
      {/* Top Banner: Siting Optimizer Controls */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <Award className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white tracking-tight">
                Cooling Center Siting Optimization
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Multi-objective prioritization fusing BigQuery ML spatial heat offsets with Census poverty and vehicle deprivation.
            </p>
          </div>

          {/* Interactive Scenario Controls */}
          <div className="flex flex-wrap items-center gap-4 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            {/* Funding Allocation (N Centers) */}
            <div className="text-xs">
              <span className="text-slate-400 block mb-1">Funded Siting Slots:</span>
              <div className="flex space-x-1">
                {[2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setFundingSlots(n)}
                    className={`px-3 py-1 rounded-md text-xs font-semibold font-mono transition-all ${
                      fundingSlots === n
                        ? 'bg-rose-600 text-white shadow'
                        : 'bg-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    Top {n}
                  </button>
                ))}
              </div>
            </div>

            {/* City Baseline Forecast Slider */}
            <div className="text-xs min-w-[200px]">
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Citywide Forecast:</span>
                <span className="font-mono font-bold text-amber-400">{forecastBaselineF}°F</span>
              </div>
              <input
                type="range"
                min="85"
                max="105"
                step="1"
                value={forecastBaselineF}
                onChange={(e) => setForecastBaselineF(parseInt(e.target.value))}
                className="w-full accent-amber-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Formula Toggle Details */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <button
            onClick={() => setShowFormulaDetails(!showFormulaDetails)}
            className="flex items-center space-x-1 text-slate-300 hover:text-white"
          >
            <Sliders className="w-3.5 h-3.5 text-slate-400" />
            <span>Composite Siting Score Formula: <b>0.4 × Offset + 0.3 × Poverty + 0.3 × Carless</b></span>
          </button>
          <span className="text-slate-500 font-mono text-[11px]">Calibrated for Atlanta Heat Watch 2026</span>
        </div>

        {showFormulaDetails && (
          <div className="mt-3 p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-1">
            <p className="font-semibold text-rose-300">Objective Function Rationale:</p>
            <p>
              • <b>Thermal Exposure (40%):</b> Direct microclimate offset (°F) predicted by BQML <code className="text-amber-400">heat_offset_model</code>.
            </p>
            <p>
              • <b>Economic Vulnerability (30%):</b> Tract poverty rate reflects household inability to afford residential AC utility burdens.
            </p>
            <p>
              • <b>Mobility & Transit Deprivation (30%):</b> Share of carless households determining reliance on 10-minute pedestrian walk access to public cooling facilities.
            </p>
          </div>
        )}
      </div>

      {/* Ranked Candidate Cards Table */}
      <div className="grid grid-cols-1 gap-4">
        {rankings.map((site) => {
          const isFunded = site.rank <= fundingSlots;
          const localizedTemp = (forecastBaselineF + site.predictedOffsetF).toFixed(1);

          return (
            <div
              key={site.tractId}
              onClick={() => onSelectRanking(site)}
              className={`p-5 rounded-xl border transition-all cursor-pointer ${
                isFunded
                  ? 'bg-slate-900/90 border-rose-500/40 hover:border-rose-400 shadow-lg shadow-rose-950/20'
                  : 'bg-slate-950/60 border-slate-800/80 opacity-75 hover:opacity-100 hover:border-slate-700'
              }`}
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                {/* Rank & Facility Info */}
                <div className="flex items-start space-x-4">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center font-mono font-bold text-lg flex-shrink-0 ${
                      isFunded
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                    }`}
                  >
                    #{site.rank}
                  </div>

                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-bold text-white text-base">{site.name}</h3>
                      {isFunded && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center space-x-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Funded Candidate</span>
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-400 flex items-center space-x-3 mt-1">
                      <span>{site.neighborhood}</span>
                      <span>•</span>
                      <span className="font-mono text-slate-500">Tract {site.tractId}</span>
                      <span>•</span>
                      <span className="flex items-center space-x-1 text-sky-400">
                        <Footprints className="w-3 h-3" />
                        <span>{site.walkAccessMinutes} min walk</span>
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-2 italic max-w-2xl">
                      "{site.sitingJustification}"
                    </p>
                  </div>
                </div>

                {/* Score & Heat Offset Metrics */}
                <div className="flex items-center space-x-4 border-t lg:border-t-0 pt-3 lg:pt-0 border-slate-800 flex-shrink-0">
                  <div className="text-right">
                    <div className="text-xs text-slate-400">Microclimate Temp</div>
                    <div className="text-xl font-mono font-bold text-rose-400 flex items-center justify-end space-x-1">
                      <Thermometer className="w-4 h-4 text-rose-500" />
                      <span>{localizedTemp}°F</span>
                    </div>
                    <div className="text-[10px] text-amber-400 font-mono">
                      (+{site.predictedOffsetF}°F offset)
                    </div>
                  </div>

                  <div className="text-right pl-3 border-l border-slate-800">
                    <div className="text-xs text-slate-400">Poverty / Carless</div>
                    <div className="text-sm font-mono font-bold text-slate-200">
                      {site.povertyRatePct}% / {site.noVehicleRatePct}%
                    </div>
                    <div className="text-[10px] text-emerald-400 font-mono">
                      Score: {site.compositeScore.toFixed(2)}
                    </div>
                  </div>

                  <ChevronRight className="w-5 h-5 text-slate-600 hidden lg:block" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Action Decision Dock: Audit Outcome & Draft Council Memo */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <ShieldAlert className="w-5 h-5 text-emerald-400" />
          <div>
            <div className="text-xs font-bold text-white">Next Operational Steps:</div>
            <div className="text-[11px] text-slate-400">
              Validate climate equity benchmarks or generate legislative resolution for Council.
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <button
            onClick={() => onAuditRecommendations(selectedCandidates)}
            className="flex-1 sm:flex-none px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition-all flex items-center justify-center space-x-1.5"
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Audit Equity on Top {fundingSlots}</span>
          </button>
          <button
            onClick={() => onDraftCouncilProposal(selectedCandidates)}
            className="flex-1 sm:flex-none px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow transition-all flex items-center justify-center space-x-1.5"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Draft Council Resolution</span>
          </button>
        </div>
      </div>
    </div>
  );
};
