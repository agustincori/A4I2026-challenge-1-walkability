import React, { useEffect, useRef, useState, useMemo } from 'react';
import L from 'leaflet';
import { CensusTract, DispatchedAsset } from '../types';
import { Flame, Users, Navigation, AlertTriangle, Sparkles, Building, Info, Search, Crosshair, Trees, ShieldAlert, X, Truck } from 'lucide-react';

interface HeatMapProps {
  tracts: CensusTract[];
  selectedTract: CensusTract | null;
  onSelectTract: (tract: CensusTract) => void;
  onAskAgentAboutTract: (tract: CensusTract) => void;
  forecastBaselineF: number;
  dispatchedAssets?: DispatchedAsset[];
}

export const HeatMap: React.FC<HeatMapProps> = ({
  tracts,
  selectedTract,
  onSelectTract,
  onAskAgentAboutTract,
  forecastBaselineF,
  dispatchedAssets = [],
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isSearchFocused, setIsSearchFocused] = useState<boolean>(false);
  const [minOffsetFilter, setMinOffsetFilter] = useState<number>(-3);
  const [minPovertyFilter, setMinPovertyFilter] = useState<number>(0);
  const [showWalkBuffers, setShowWalkBuffers] = useState<boolean>(true);
  const [onlyCandidates, setOnlyCandidates] = useState<boolean>(false);
  const [showDispatchedAssets, setShowDispatchedAssets] = useState<boolean>(true);

  // Filtered tracts for search autocomplete
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase().trim();
    return tracts
      .filter(
        (t) =>
          t.neighborhood.toLowerCase().includes(q) ||
          t.name.toLowerCase().includes(q) ||
          t.geoId.includes(q) ||
          (t.coolingCenterName && t.coolingCenterName.toLowerCase().includes(q))
      )
      .slice(0, 7);
  }, [tracts, searchQuery]);

  // Color helper based on predicted offset
  const getOffsetColor = (offset: number) => {
    if (offset >= 4.0) return '#ef4444'; // Red extreme
    if (offset >= 2.5) return '#f97316'; // Orange high
    if (offset >= 0.5) return '#eab308'; // Amber medium
    if (offset >= -0.5) return '#38bdf8'; // Sky neutral
    return '#22c55e'; // Green cool
  };

  const handleSelectAndFly = (tract: CensusTract) => {
    onSelectTract(tract);
    setSearchQuery('');
    setIsSearchFocused(false);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([tract.latitude, tract.longitude], 14, {
        duration: 1.0,
      });
    }
  };

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [33.755, -84.39],
        zoom: 12,
        zoomControl: false,
      });

      L.control.zoom({ position: 'topright' }).addTo(map);

      // Dark theme tiles suitable for urban heat resilience
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap',
        maxZoom: 19,
      }).addTo(map);

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;
      mapInstanceRef.current = map;
    }

    return () => {
      // Map cleanup if needed
    };
  }, []);

  // Update markers and buffers when tracts or filters change
  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current) return;

    layerGroupRef.current.clearLayers();

    const filtered = tracts.filter((t) => {
      if (t.predictedOffsetF < minOffsetFilter) return false;
      if (t.povertyRatePct < minPovertyFilter) return false;
      if (onlyCandidates && !t.hasCoolingCenter) return false;
      return true;
    });

    filtered.forEach((tract) => {
      const color = getOffsetColor(tract.predictedOffsetF);
      const isSelected = selectedTract?.geoId === tract.geoId;

      // Draw tract heat footprint circle
      const circle = L.circleMarker([tract.latitude, tract.longitude], {
        radius: isSelected ? 18 : 13,
        fillColor: color,
        color: isSelected ? '#ffffff' : color,
        weight: isSelected ? 3 : 1.5,
        opacity: 0.9,
        fillOpacity: isSelected ? 0.9 : 0.65,
      });

      // Tooltip
      circle.bindTooltip(
        `<div class="p-1 font-sans text-xs">
          <div class="font-bold text-slate-900">${tract.neighborhood}</div>
          <div class="text-slate-700">Offset: <b>${tract.predictedOffsetF > 0 ? '+' : ''}${tract.predictedOffsetF}°F</b></div>
          <div class="text-slate-700">Canopy: <b>${tract.treeCanopyPct ?? 'N/A'}%</b> | SVI: <b>${tract.sviScore ? (tract.sviScore * 100).toFixed(0) + 'th %ile' : 'N/A'}</b></div>
          <div class="text-slate-700">Poverty: <b>${tract.povertyRatePct}%</b> | No Car: <b>${tract.noVehicleRatePct}%</b></div>
        </div>`,
        { direction: 'top', className: 'rounded shadow-md' }
      );

      circle.on('click', () => {
        onSelectTract(tract);
      });

      layerGroupRef.current?.addLayer(circle);

      // Add 10-minute walk buffer (800 meters) around candidate cooling center sites
      if (showWalkBuffers && tract.hasCoolingCenter) {
        const buffer = L.circle([tract.latitude, tract.longitude], {
          radius: 800, // 800m is approximately a 10-minute walk
          fillColor: '#0ea5e9',
          color: '#0284c7',
          weight: 1.5,
          dashArray: '4, 4',
          fillOpacity: 0.1,
        });
        buffer.bindTooltip(`10-minute walk buffer (800m) to ${tract.coolingCenterName}`, {
          direction: 'bottom',
        });
        layerGroupRef.current?.addLayer(buffer);
      }
    });

    // Render active mobile dispatched assets (Resource Mover)
    if (showDispatchedAssets && dispatchedAssets && dispatchedAssets.length > 0) {
      dispatchedAssets.forEach((asset) => {
        const iconEmoji = asset.type === 'hydration' ? '💧' : asset.type === 'wellness' ? '🚑' : '🚌';
        const colorClass =
          asset.type === 'hydration'
            ? 'background:#d97706;'
            : asset.type === 'wellness'
            ? 'background:#4f46e5;'
            : 'background:#0891b2;';

        const customIcon = L.divIcon({
          html: `<div style="display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:9999px;border:2px solid #ffffff;box-shadow:0 4px 12px rgba(0,0,0,0.6);font-size:14px;cursor:pointer;${colorClass}">${iconEmoji}</div>`,
          className: 'custom-asset-pin',
          iconSize: [30, 30],
          iconAnchor: [15, 15],
        });

        const marker = L.marker([asset.lat, asset.lng], { icon: customIcon });
        marker.bindTooltip(
          `<div style="font-family:sans-serif;font-size:12px;padding:2px;">
            <b style="color:#ffffff;">${asset.name}</b><br/>
            <span style="color:#94a3b8;">${asset.locationName}</span><br/>
            <span style="color:#34d399;">+${asset.protectedPopulation.toLocaleString()} residents protected</span>
          </div>`,
          { direction: 'top', offset: [0, -15] }
        );
        layerGroupRef.current?.addLayer(marker);
      });
    }
  }, [
    tracts,
    selectedTract,
    minOffsetFilter,
    minPovertyFilter,
    showWalkBuffers,
    onlyCandidates,
    showDispatchedAssets,
    dispatchedAssets,
    onSelectTract,
  ]);

  // Sync map center when selectedTract changes from external interactions
  useEffect(() => {
    if (selectedTract && mapInstanceRef.current) {
      mapInstanceRef.current.panTo([selectedTract.latitude, selectedTract.longitude], {
        animate: true,
        duration: 0.8,
      });
    }
  }, [selectedTract]);

  return (
    <div className="relative w-full h-[calc(100vh-8.5rem)] rounded-xl overflow-hidden border border-slate-800 bg-slate-950 flex flex-col md:flex-row">
      {/* Top Search & Filter Bar */}
      <div className="absolute top-4 left-4 z-[400] w-72 sm:w-84 space-y-2">
        {/* Landmark / Neighborhood Search */}
        <div className="relative bg-slate-900/95 backdrop-blur border border-slate-700/80 rounded-xl shadow-2xl p-1.5">
          <div className="flex items-center px-2 py-1 space-x-2">
            <Search className="w-4 h-4 text-slate-400 shrink-0" />
            <input
              type="text"
              placeholder="Search neighborhood, street, or tract..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
              className="w-full bg-transparent text-xs text-white placeholder-slate-400 focus:outline-none"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Autocomplete Dropdown */}
          {isSearchFocused && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1.5 bg-slate-900/98 border border-slate-700/80 rounded-xl shadow-2xl overflow-hidden z-50">
              <div className="text-[10px] uppercase font-bold text-slate-400 px-3 py-1.5 border-b border-slate-800 bg-slate-950/50">
                Matching Atlanta Tracts ({searchResults.length})
              </div>
              {searchResults.map((tract) => (
                <button
                  key={tract.geoId}
                  type="button"
                  onClick={() => handleSelectAndFly(tract)}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800/80 border-b border-slate-800/40 flex items-center justify-between text-xs transition-colors"
                >
                  <div className="truncate pr-2">
                    <span className="font-semibold text-slate-200 block truncate">{tract.neighborhood}</span>
                    <span className="text-[10px] text-slate-400 font-mono">Tract {tract.geoId} · Canopy {tract.treeCanopyPct ?? '--'}%</span>
                  </div>
                  <span
                    className={`font-mono font-bold text-[11px] px-1.5 py-0.5 rounded ${
                      tract.predictedOffsetF >= 3.5
                        ? 'bg-rose-500/20 text-rose-400'
                        : tract.predictedOffsetF >= 1.0
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-emerald-500/20 text-emerald-400'
                    }`}
                  >
                    {tract.predictedOffsetF > 0 ? `+${tract.predictedOffsetF}°F` : `${tract.predictedOffsetF}°F`}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Spatial Heat & Walk Filters Panel */}
        <div className="bg-slate-900/90 backdrop-blur border border-slate-700/70 p-3 rounded-xl shadow-xl hidden sm:block">
          <div className="flex items-center space-x-2 mb-2 pb-1 border-b border-slate-800">
            <Flame className="w-4 h-4 text-rose-400" />
            <h4 className="text-xs font-bold text-slate-100 uppercase tracking-wider">Spatial Heat & Walk Filters</h4>
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Min Offset:</span>
                <span className="font-mono font-bold text-rose-400">
                  {minOffsetFilter > 0 ? `+${minOffsetFilter}°F` : `${minOffsetFilter}°F`}
                </span>
              </div>
              <input
                type="range"
                min="-3"
                max="4.5"
                step="0.5"
                value={minOffsetFilter}
                onChange={(e) => setMinOffsetFilter(parseFloat(e.target.value))}
                className="w-full accent-rose-500 h-1.5 bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-300 mb-1">
                <span>Min Poverty Rate:</span>
                <span className="font-mono font-bold text-amber-400">{minPovertyFilter}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="45"
                step="5"
                value={minPovertyFilter}
                onChange={(e) => setMinPovertyFilter(parseFloat(e.target.value))}
                className="w-full accent-amber-500 h-1.5 bg-slate-700 rounded-lg cursor-pointer"
              />
            </div>

            <div className="flex flex-col gap-1.5 pt-1">
              <div className="flex items-center justify-between">
                <label className="flex items-center space-x-1.5 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showWalkBuffers}
                    onChange={(e) => setShowWalkBuffers(e.target.checked)}
                    className="rounded accent-sky-500 text-sky-500"
                  />
                  <span>10-min Walk Buffers</span>
                </label>

                <label className="flex items-center space-x-1.5 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={onlyCandidates}
                    onChange={(e) => setOnlyCandidates(e.target.checked)}
                    className="rounded accent-rose-500 text-rose-500"
                  />
                  <span>Siting Sites Only</span>
                </label>
              </div>

              <label className="flex items-center space-x-1.5 text-slate-300 cursor-pointer pt-0.5">
                <input
                  type="checkbox"
                  checked={showDispatchedAssets}
                  onChange={(e) => setShowDispatchedAssets(e.target.checked)}
                  className="rounded accent-emerald-500 text-emerald-500"
                />
                <span className="flex items-center gap-1 text-emerald-300">
                  <Truck className="w-3 h-3 text-emerald-400" />
                  <span>Mobile Assets ({dispatchedAssets.length})</span>
                </span>
              </label>
            </div>
          </div>

          {/* Legend */}
          <div className="mt-3 pt-2 border-t border-slate-800 text-[11px] flex items-center justify-between">
            <span className="text-slate-400">Thermal Offset:</span>
            <div className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" title="< -0.5°F"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-sky-400" title="0°F Baseline"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" title="+1°F to +2°F"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500" title="+2.5°F to +3.9°F"></span>
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" title="+4°F+ Extreme"></span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Map Canvas */}
      <div className="flex-1 h-full relative" onClick={() => setIsSearchFocused(false)}>
        <div ref={mapContainerRef} className="w-full h-full z-10" />
      </div>

      {/* Interactive Selected Tract Inspector Drawer */}
      {selectedTract ? (
        <div className="w-full md:w-96 bg-slate-900 border-t md:border-t-0 md:border-l border-slate-800 p-5 overflow-y-auto flex flex-col justify-between z-20">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <span className="text-xs font-mono text-slate-400">TRACT {selectedTract.geoId}</span>
                <h3 className="text-base font-bold text-white leading-tight">{selectedTract.neighborhood}</h3>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  title="Focus on Map"
                  onClick={() => {
                    if (mapInstanceRef.current) {
                      mapInstanceRef.current.flyTo([selectedTract.latitude, selectedTract.longitude], 14, { duration: 0.8 });
                    }
                  }}
                  className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  <Crosshair className="w-4 h-4" />
                </button>
                <span
                  className={`px-2 py-1 rounded text-xs font-bold font-mono ${
                    selectedTract.predictedOffsetF >= 3.5
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : selectedTract.predictedOffsetF >= 1.0
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  }`}
                >
                  {selectedTract.predictedOffsetF > 0 ? `+${selectedTract.predictedOffsetF}°F` : `${selectedTract.predictedOffsetF}°F`}
                </span>
              </div>
            </div>

            {/* Localized Temperature Calculator against Current City Baseline */}
            <div className="mt-4 p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>City Forecast Baseline:</span>
                <span className="font-mono text-slate-200">{forecastBaselineF}°F</span>
              </div>
              <div className="flex justify-between items-center mt-1 text-sm font-semibold">
                <span className="text-slate-300">Predicted Microclimate:</span>
                <span className="font-mono text-rose-400 text-lg">
                  {(forecastBaselineF + selectedTract.predictedOffsetF).toFixed(1)}°F
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-1 italic">
                *Tract runs {Math.abs(selectedTract.predictedOffsetF)}°F {selectedTract.predictedOffsetF >= 0 ? 'hotter' : 'cooler'} than citywide baseline.
              </div>
            </div>

            {/* Tree Canopy & SVI Environmental Justice Cards */}
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30">
                <div className="flex items-center space-x-1.5 text-xs text-emerald-300 mb-1">
                  <Trees className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Tree Canopy</span>
                </div>
                <div className="text-base font-bold text-white font-mono">
                  {selectedTract.treeCanopyPct !== undefined ? `${selectedTract.treeCanopyPct}%` : '36.5%'}
                </div>
                <span className="text-[10px] text-slate-400">City Avg: 36.5%</span>
              </div>

              <div className="p-2.5 rounded-lg bg-purple-950/30 border border-purple-500/30">
                <div className="flex items-center space-x-1.5 text-xs text-purple-300 mb-1">
                  <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
                  <span>CDC SVI Rank</span>
                </div>
                <div className="text-base font-bold text-white font-mono">
                  {selectedTract.sviScore !== undefined ? `${(selectedTract.sviScore * 100).toFixed(0)}th %ile` : 'High'}
                </div>
                <span className="text-[10px] text-slate-400">
                  {selectedTract.integratedRiskScore ? `Risk: ${selectedTract.integratedRiskScore.toFixed(1)}/100` : 'Composite High'}
                </span>
              </div>
            </div>

            {/* Vulnerability Metrics Grid */}
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>Poverty Rate</span>
                </div>
                <div className="text-base font-bold text-slate-100 font-mono">
                  {selectedTract.povertyRatePct}%
                </div>
                <span className="text-[10px] text-slate-400">P75 Threshold: 24.5%</span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
                  <Navigation className="w-3.5 h-3.5 text-sky-400" />
                  <span>No Vehicle</span>
                </div>
                <div className="text-base font-bold text-slate-100 font-mono">
                  {selectedTract.noVehicleRatePct}%
                </div>
                <span className="text-[10px] text-slate-400">P75 Threshold: 14.8%</span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
                  <Users className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Population</span>
                </div>
                <div className="text-base font-bold text-slate-100 font-mono">
                  {selectedTract.totalPop.toLocaleString()}
                </div>
                <span className="text-[10px] text-slate-400">Median Age: {selectedTract.medianAge}y</span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
                <div className="flex items-center space-x-1.5 text-xs text-slate-400 mb-1">
                  <Building className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Vintage</span>
                </div>
                <div className="text-base font-bold text-slate-100 font-mono">
                  {selectedTract.medianYearBuilt}
                </div>
                <span className="text-[10px] text-slate-400">{selectedTract.housingUnits ?? 0} housing units</span>
              </div>
            </div>

            {/* Existing / Recommended Cooling Center status */}
            {selectedTract.hasCoolingCenter && (
              <div className="mt-3 p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-xs">
                <div className="font-bold text-emerald-300 flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>Identified Cooling Siting Candidate</span>
                </div>
                <p className="text-slate-300 mt-1 font-semibold">{selectedTract.coolingCenterName}</p>
                <div className="flex items-center justify-between text-slate-400 text-[11px] mt-1 pt-1 border-t border-emerald-900/40">
                  <span>Type: {selectedTract.coolingCenterType}</span>
                  <span>10-min Walk Score: {selectedTract.walkScore}/100</span>
                </div>
              </div>
            )}
          </div>

          {/* Action CTA: Consult AI Advisor */}
          <div className="pt-3 border-t border-slate-800 mt-3">
            <button
              onClick={() => onAskAgentAboutTract(selectedTract)}
              className="w-full py-2.5 px-3 rounded-lg bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white font-medium text-xs flex items-center justify-center space-x-2 shadow-lg shadow-rose-950/50 transition-all"
            >
              <Sparkles className="w-4 h-4" />
              <span>Query Advisor on {selectedTract.neighborhood}</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="hidden md:flex w-80 bg-slate-900 border-l border-slate-800 p-6 flex-col items-center justify-center text-center text-slate-500">
          <Info className="w-10 h-10 mb-3 text-slate-600" />
          <h4 className="text-sm font-semibold text-slate-400">Click Any Census Tract</h4>
          <p className="text-xs text-slate-500 mt-1">
            Search above or click any point on the Atlanta map to inspect microclimate heat offsets, tree canopy %, SVI vulnerability, and 10-minute walk buffers.
          </p>
        </div>
      )}
    </div>
  );
};
