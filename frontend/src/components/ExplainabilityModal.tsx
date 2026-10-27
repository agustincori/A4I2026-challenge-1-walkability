import React from 'react';
import { MOCK_FEATURE_ATTRIBUTIONS } from '../data/mockData';
import { CensusTract } from '../types';
import { X, Sparkles, AlertCircle, Trees, Building2, Car, Compass } from 'lucide-react';

interface ExplainabilityModalProps {
  isOpen: boolean;
  onClose: () => void;
  tract: CensusTract | null;
}

export const ExplainabilityModal: React.FC<ExplainabilityModalProps> = ({
  isOpen,
  onClose,
  tract,
}) => {
  if (!isOpen || !tract) return null;

  const attributions = MOCK_FEATURE_ATTRIBUTIONS;

  const getFeatureIcon = (feature: string) => {
    if (feature.toLowerCase().includes('tree') || feature.toLowerCase().includes('canopy')) {
      return <Trees className="w-4 h-4 text-emerald-400" />;
    }
    if (feature.toLowerCase().includes('building') || feature.toLowerCase().includes('vintage')) {
      return <Building2 className="w-4 h-4 text-amber-400" />;
    }
    if (feature.toLowerCase().includes('disinvestment') || feature.toLowerCase().includes('density')) {
      return <Car className="w-4 h-4 text-rose-400" />;
    }
    return <Compass className="w-4 h-4 text-sky-400" />;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Sparkles className="w-5 h-5" />
            </span>
            <div>
              <h3 className="text-lg font-bold text-white">
                ML.EXPLAIN_PREDICT Microclimate Attribution
              </h3>
              <p className="text-xs text-slate-400">
                {tract.neighborhood} (Tract {tract.geoId}) • Predicted Offset: <b>+{tract.predictedOffsetF}°F</b>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Explainability Body */}
        <div className="space-y-4 my-5">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p>
              Rather than treating the prediction as a black box, BigQuery ML calculates exact feature contributions showing why this tract warms {tract.predictedOffsetF}°F above the citywide baseline.
            </p>
          </div>

          {/* Feature List */}
          <div className="space-y-3">
            {attributions.map((attr, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2">
                    {getFeatureIcon(attr.feature)}
                    <span className="text-xs font-semibold text-slate-200">{attr.feature}</span>
                  </div>
                  <span className="font-mono font-bold text-xs text-rose-400">
                    +{attr.attributionF}°F
                  </span>
                </div>
                <p className="text-xs text-slate-400">{attr.baselineContribution}</p>

                {/* Contribution relative bar */}
                <div className="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-rose-500 h-full rounded-full"
                    style={{ width: `${(attr.attributionF / 2.0) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-all"
          >
            Close Attribution View
          </button>
        </div>
      </div>
    </div>
  );
};
