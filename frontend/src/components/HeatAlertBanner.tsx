import React, { useState } from 'react';
import { ShieldAlert, X, CheckCircle2 } from 'lucide-react';
import { HeatAlert } from '../types';

interface HeatAlertBannerProps {
  alerts: HeatAlert[];
  baselineTempF: number;
}

export const HeatAlertBanner: React.FC<HeatAlertBannerProps> = ({ alerts, baselineTempF }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      {/* Alert Ticker Bar */}
      <div className="bg-gradient-to-r from-amber-950/90 via-rose-950/90 to-red-950/90 border-b border-rose-800/40 px-4 py-2 flex items-center justify-between text-xs z-40 relative">
        <div className="flex items-center gap-3 overflow-hidden">
          <span className="flex h-2.5 w-2.5 relative shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
          </span>
          <span className="bg-rose-500/20 text-rose-300 font-semibold px-2 py-0.5 rounded border border-rose-500/40 uppercase tracking-wide text-[10px] shrink-0">
            NWS Heat Advisory Stage 3
          </span>
          <div className="truncate text-slate-200">
            <span className="font-semibold text-amber-200">Metro Heat Index: {(baselineTempF + 2.6).toFixed(1)}°F</span>
            <span className="mx-2 text-slate-500">•</span>
            <span>Hotspots Active: Thomasville Heights (+1.26°F), Bankhead (+0.98°F), Campbellton (+1.30°F)</span>
            <span className="mx-2 text-slate-500">•</span>
            <span className="text-rose-300 font-medium">Transit wait-time exposure risk: Severe</span>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0 ml-3">
          <span className="text-slate-400 hidden sm:inline text-[11px]">
            Baseline: <strong className="text-white font-mono">{baselineTempF.toFixed(1)}°F</strong>
          </span>
          <button
            onClick={() => setIsModalOpen(true)}
            className="text-rose-300 hover:text-white underline text-xs font-semibold cursor-pointer whitespace-nowrap"
          >
            View {alerts.length} Alerts
          </button>
        </div>
      </div>

      {/* Alerts Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <span className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <ShieldAlert className="w-5 h-5" />
                </span>
                <div>
                  <h3 className="font-bold text-white text-base">Active Municipal Heat Advisories</h3>
                  <p className="text-xs text-slate-400">Emergency Operations Center • City of Atlanta</p>
                </div>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3.5 my-4 max-h-[60vh] overflow-y-auto pr-1">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3.5 rounded-xl border ${
                    alert.severity === 'warning'
                      ? 'bg-rose-950/30 border-rose-800/40 text-rose-200'
                      : alert.severity === 'spike'
                      ? 'bg-amber-950/30 border-amber-800/40 text-amber-200'
                      : 'bg-indigo-950/30 border-indigo-800/40 text-indigo-200'
                  }`}
                >
                  <div className="flex justify-between items-center text-xs font-bold mb-1">
                    <span className="tracking-tight text-white">{alert.title}</span>
                    <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-950/60 border border-slate-700 text-slate-300">
                      {alert.zone}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 mb-2 leading-relaxed">{alert.description}</p>
                  <div className="flex items-start gap-1.5 text-[11px] font-medium text-emerald-300 bg-slate-950/40 p-2 rounded-lg border border-emerald-900/40">
                    <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-400" />
                    <span>{alert.recommendation}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setIsModalOpen(false)}
                className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-xl text-xs font-semibold transition"
              >
                Acknowledge Directives
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
