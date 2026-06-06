"use client";

import React, { useState, useMemo } from 'react';
import nigeriaMap from '@svg-maps/nigeria';

// Generate stable mock data so it doesn't flicker on mousemove
const generateStableData = () => {
  const data: Record<string, { incidents: number; status: string; riskLevel: 'low' | 'medium' | 'high' }> = {};
  
  nigeriaMap.locations.forEach((loc: any) => {
    // Generate a pseudo-random but stable number based on string length and char codes
    let hash = 0;
    for (let i = 0; i < loc.name.length; i++) {
      hash += loc.name.charCodeAt(i);
    }
    
    const incidents = hash % 25;
    let riskLevel: 'low' | 'medium' | 'high' = 'low';
    let status = 'Normal';
    
    if (incidents > 15) {
      riskLevel = 'high';
      status = 'High Alert';
    } else if (incidents > 5) {
      riskLevel = 'medium';
      status = 'Elevated Risk';
    }
    
    data[loc.name] = { incidents, status, riskLevel };
  });
  
  // Hardcode a few specific well-known hotspots for demonstration realism
  data['Borno'] = { incidents: 42, status: 'Critical Alert', riskLevel: 'high' };
  data['Kaduna'] = { incidents: 28, status: 'High Alert', riskLevel: 'high' };
  data['Lagos'] = { incidents: 5, status: 'Normal', riskLevel: 'low' };
  data['Federal Capital Territory'] = { incidents: 2, status: 'Secured', riskLevel: 'low' };

  return data;
};

export default function InteractiveMap() {
  const [hoveredState, setHoveredState] = useState<string | null>(null);
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const stateData = useMemo(() => generateStableData(), []);

  const handleLocationMouseOver = (event: React.MouseEvent<SVGPathElement>, name: string) => {
    setHoveredState(name);
  };

  const handleLocationMouseOut = () => {
    setHoveredState(null);
  };

  const handleLocationMouseMove = (event: React.MouseEvent<SVGPathElement>) => {
    setTooltipPos({ x: event.clientX, y: event.clientY });
  };

  const handleLocationClick = (event: React.MouseEvent<SVGPathElement>, name: string) => {
    if (name === selectedState) {
      setSelectedState(null);
    } else {
      setSelectedState(name);
    }
  };

  return (
    <div className="relative w-full max-w-5xl mx-auto p-6 bg-slate-900 rounded-xl shadow-2xl border border-slate-800">
      <div className="flex flex-col md:flex-row justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Geographic Threat Intelligence</h2>
        <div className="flex gap-4 mt-4 md:mt-0 text-sm">
          <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-slate-700"></div><span className="text-slate-400">Low</span></div>
          <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-400"></div><span className="text-slate-400">Elevated</span></div>
          <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-600"></div><span className="text-slate-400">High Risk</span></div>
        </div>
      </div>
      
      <div className="w-full flex justify-center">
        <svg 
          viewBox={nigeriaMap.viewBox} 
          className="w-full h-auto max-h-[650px] drop-shadow-md"
          aria-label={nigeriaMap.label}
        >
          {nigeriaMap.locations.map((location: any) => {
            const isHovered = hoveredState === location.name;
            const isSelected = selectedState === location.name;
            const data = stateData[location.name];
            
            // Base risk colors
            let baseFill = "fill-slate-700";
            if (data?.riskLevel === 'medium') baseFill = "fill-red-900/40";
            if (data?.riskLevel === 'high') baseFill = "fill-red-800/80";

            // Interaction overrides
            if (isSelected) baseFill = "fill-red-500";
            else if (isHovered) baseFill = "fill-red-400";

            return (
              <path
                key={location.id}
                id={location.id}
                name={location.name}
                d={location.path}
                className={`cursor-pointer transition-all duration-300 focus:outline-none stroke-slate-900 stroke-[1] ${baseFill}`}
                onMouseOver={(e) => handleLocationMouseOver(e, location.name)}
                onMouseOut={handleLocationMouseOut}
                onMouseMove={handleLocationMouseMove}
                onClick={(e) => handleLocationClick(e, location.name)}
              />
            );
          })}
        </svg>
      </div>

      {hoveredState && stateData[hoveredState] && (
        <div
          className="fixed pointer-events-none z-50 px-4 py-3 bg-slate-800/95 backdrop-blur-sm text-white text-sm rounded-lg shadow-2xl border border-slate-700 flex flex-col gap-1 min-w-[150px]"
          style={{
            left: `${tooltipPos.x + 20}px`,
            top: `${tooltipPos.y + 20}px`,
          }}
        >
          <span className="font-bold text-slate-100 text-base mb-1">{hoveredState}</span>
          <div className="flex justify-between items-center gap-4">
            <span className="text-slate-400">Incidents</span>
            <span className="font-mono font-semibold text-red-400">{stateData[hoveredState].incidents}</span>
          </div>
          <div className="flex justify-between items-center gap-4">
            <span className="text-slate-400">Status</span>
            <span className={`font-semibold ${stateData[hoveredState].riskLevel === 'high' ? 'text-red-500' : stateData[hoveredState].riskLevel === 'medium' ? 'text-orange-400' : 'text-emerald-400'}`}>
              {stateData[hoveredState].status}
            </span>
          </div>
        </div>
      )}

      {selectedState && stateData[selectedState] && (
        <div className="mt-8 p-6 bg-slate-800/50 rounded-xl border border-slate-700 backdrop-blur-md transition-all animate-in fade-in slide-in-from-bottom-4">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-2xl font-bold text-white mb-1">{selectedState} Region Profile</h3>
              <p className="text-slate-400 text-sm">Detailed intelligence reporting for {selectedState}.</p>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
              stateData[selectedState].riskLevel === 'high' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 
              stateData[selectedState].riskLevel === 'medium' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' : 
              'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
            }`}>
              {stateData[selectedState].status}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
            <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
              <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Total Incidents (30d)</p>
              <p className="text-3xl font-mono text-slate-100">{stateData[selectedState].incidents}</p>
            </div>
            <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
              <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Trend</p>
              <p className="text-xl text-slate-100 mt-1">{stateData[selectedState].incidents > 10 ? '↗ Escalating' : '↘ Stabilizing'}</p>
            </div>
            <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
              <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Primary Threat Vector</p>
              <p className="text-xl text-slate-100 mt-1">{stateData[selectedState].riskLevel === 'high' ? 'Armed Groups' : 'Civil Unrest'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
