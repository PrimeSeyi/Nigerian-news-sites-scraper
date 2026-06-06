"use client";

import React, { useState } from 'react';
import Nigeria from '@svg-maps/nigeria';
import { SVGMap } from 'react-svg-map';
import 'react-svg-map/lib/index.css';

export default function InteractiveMap() {
  const [hoveredState, setHoveredState] = useState<string | null>(null);
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const handleLocationMouseOver = (event: React.MouseEvent<SVGElement>) => {
    const pointedLocation = event.target as SVGElement;
    setHoveredState(pointedLocation.getAttribute('name'));
  };

  const handleLocationMouseOut = () => {
    setHoveredState(null);
  };

  const handleLocationMouseMove = (event: React.MouseEvent<SVGElement>) => {
    setTooltipPos({ x: event.clientX, y: event.clientY });
  };

  const handleLocationClick = (event: React.MouseEvent<SVGElement>) => {
    const pointedLocation = event.target as SVGElement;
    const stateName = pointedLocation.getAttribute('name');
    if (stateName === selectedState) {
      setSelectedState(null); // Toggle off
    } else {
      setSelectedState(stateName);
    }
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto p-4 bg-slate-900 rounded-lg shadow-xl border border-slate-800">
      <h2 className="text-xl font-bold text-slate-200 mb-4 text-center">Interactive Map of Nigeria</h2>
      
      <div className="svg-map-container">
        <SVGMap
          map={Nigeria}
          onLocationMouseOver={handleLocationMouseOver}
          onLocationMouseOut={handleLocationMouseOut}
          onLocationMouseMove={handleLocationMouseMove}
          onLocationClick={handleLocationClick}
          locationClassName={(location: any) => {
            const isHovered = hoveredState === location.name;
            const isSelected = selectedState === location.name;
            let baseClass = "cursor-pointer transition-colors duration-200 focus:outline-none stroke-slate-800 stroke-[0.5]";
            
            if (isSelected) {
              return `${baseClass} fill-red-500`;
            }
            if (isHovered) {
              return `${baseClass} fill-red-400`;
            }
            return `${baseClass} fill-slate-700`;
          }}
        />
      </div>

      {hoveredState && (
        <div
          className="fixed pointer-events-none z-50 px-3 py-2 bg-slate-800 text-white text-sm rounded shadow-lg border border-slate-600 flex flex-col gap-1"
          style={{
            left: `${tooltipPos.x + 15}px`,
            top: `${tooltipPos.y + 15}px`,
          }}
        >
          <span className="font-bold text-red-400">{hoveredState}</span>
          <span className="text-xs text-slate-300">Active Incidents: {Math.floor(Math.random() * 20)}</span>
          <span className="text-xs text-slate-300">Status: {Math.random() > 0.5 ? 'High Alert' : 'Normal'}</span>
        </div>
      )}

      {selectedState && (
        <div className="mt-6 p-4 bg-slate-800 rounded-md border border-slate-700">
          <h3 className="text-lg font-semibold text-red-400">{selectedState} Details</h3>
          <p className="text-slate-300 text-sm mt-2">
            Selected region data would populate here.
          </p>
        </div>
      )}
    </div>
  );
}
