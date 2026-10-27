import React from 'react';
import { MOCK_FEATURE_ATTRIBUTIONS } from '../data/mockData';
import { CensusTract } from '../types';
import { X, Sparkles, AlertCircle, Trees, Building2, Car, Compass } from 'lucide-react';
import { useModalDismiss } from '../hooks/useModalDismiss';

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
  const { modalRef, handleBackdropClick } = useModalDismiss({
    isOpen: isOpen && !!tract,
    onClose,
  });

  if (!isOpen || !tract) return null;

  const attributions = MOCK_FEATURE_ATTRIBUTIONS;

  const getFriendlyFeatureInfo = (feature: string) => {
    const f = feature.toLowerCase();
    if (f.includes('tree') || f.includes('canopy') || f.includes('pavement')) {
      return {
        icon: <Trees className="w-4 h-4 text-emerald-400" />,
        friendlyName: 'Tree Canopy Deficit & Pavement Fraction',
        plainEnglish:
          'Unshaded asphalt roads and parking lots absorb solar radiation rapidly, radiating heat back into pedestrian walkways.',
        recommendation: 'Target for rapid tree plantings, shade sails, and high-albedo cool pavements.',
      };
    }
    if (f.includes('building') || f.includes('vintage') || f.includes('construction')) {
      return {
        icon: <Building2 className="w-4 h-4 text-amber-400" />,
        friendlyName: 'Building Vintage & Thermal Mass (Pre-1970)',
        plainEnglish:
          'Older masonry and dark, uninsulated commercial roofs retain heat throughout the day and re-radiate it overnight.',
        recommendation: 'Cool-roof retrofit incentives and indoor AC assistance for residents.',
      };
    }
    if (f.includes('disinvestment') || f.includes('density') || f.includes('impervious')) {
      return {
        icon: <Car className="w-4 h-4 text-rose-400" />,
        friendlyName: 'Impervious Surface & Green Buffer Deficit',
        plainEnglish:
          'High concentration of paved surfaces without vegetative pocket parks creates a localized heat dome.',
        recommendation: 'Pocket parks, bioswales, and mobile hydration misting stations.',
      };
    }
    return {
      icon: <Compass className="w-4 h-4 text-sky-400" />,
      friendlyName: 'Basin Topography & Air Stagnation',
      plainEnglish:
        'Local elevation basins trap warm air and restrict natural convective breeze cooling during peak afternoon hours.',
      recommendation: 'Strategic placement of emergency cooling shelter shuttles and hydration units.',
    };
  };

  return (
    <div
      onClick={handleBackdropClick}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="explainability-modal-title"
    >
      <div
        ref={modalRef}
        className="relative w-full max-w-2xl max-h-[85vh] flex flex-col rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden animate-scale-in"
      >
        {/* Pinned Header */}
        <div className="flex items-center justify-between p-6 pb-4 border-b border-slate-800 shrink-0 bg-slate-900/95">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Sparkles className="w-5 h-5" />
            </span>
            <div>
              <h3 id="explainability-modal-title" className="text-base sm:text-lg font-bold text-white leading-tight">
                AI Microclimate Risk Drivers • Why is this area hotter?
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Shapley feature attribution explaining microclimate thermal variance for this tract relative to Atlanta's baseline.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Close explainability view"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Explainability Body */}
        <div className="space-y-4 p-6 py-4 flex-1 min-h-0 overflow-y-auto modal-scroll-container">
          {/* Tract Summary Badge */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-3 bg-slate-950 rounded-xl border border-slate-800">
            <div>
              <span className="text-xs font-bold text-white block">{tract.neighborhood}</span>
              <span className="text-[11px] font-mono text-slate-400">Census Tract GEOID: {tract.geoId}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-slate-400">Predicted Heat Island Offset:</span>
              <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                +{tract.predictedOffsetF}°F above baseline
              </span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              Rather than treating AI predictions as a black box, BigQuery ML calculates exact Shapley Additive Explanations (SHAP), decomposing the tract's microclimate heat into physical, addressable urban factors.
            </p>
          </div>

          {/* Feature List */}
          <div className="space-y-3">
            {attributions.map((attr, idx) => {
              const info = getFriendlyFeatureInfo(attr.feature);
              const percentage = Math.min(100, (attr.attributionF / 2.0) * 100);

              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 hover:border-slate-700 transition-colors space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {info.icon}
                      <span className="text-xs font-bold text-slate-100">{info.friendlyName}</span>
                    </div>
                    <span className="font-mono font-bold text-xs text-rose-400 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-800/40">
                      +{attr.attributionF.toFixed(2)}°F impact
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">{info.plainEnglish}</p>

                  {/* Relative contribution bar */}
                  <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-amber-500 to-rose-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                    <span>Baseline Feature: <strong className="text-slate-300 font-mono">{attr.feature}</strong></span>
                    <span className="text-emerald-400 font-medium">Mitigation: {info.recommendation}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Pinned Footer */}
        <div className="p-4 border-t border-slate-800 shrink-0 flex items-center justify-between bg-slate-900/95">
          <span className="text-xs text-slate-400">
            Powered by Vertex AI AutoML & BigQuery ML Explainability
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-all cursor-pointer"
          >
            Close Attribution View
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExplainabilityModal;
