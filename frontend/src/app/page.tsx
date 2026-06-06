"use client";

import InteractiveMap from '@/components/InteractiveMap';

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 p-8 flex flex-col items-center">
      <div className="w-full max-w-6xl mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Nigeria Security Intelligence Dashboard</h1>
        <p className="text-slate-400">Live geographic reporting and analytics.</p>
      </div>
      
      <div className="w-full max-w-6xl">
        <InteractiveMap />
      </div>
    </main>
  );
}
