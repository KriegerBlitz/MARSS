export default function Home() {
  return (
      <main className="min-h-screen p-8 max-w-7xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold tracking-tighter mb-2">MACRO-AI TERMINAL</h1>
          <p className="text-zinc-500 font-mono text-sm">Status: Connected to Live Market Feed</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 auto-rows-[200px]">
          {/* System Risk Box */}
          <div className="md:col-span-2 md:row-span-1 border border-zinc-800 bg-zinc-950 p-6 rounded-3xl flex flex-col justify-between">
            <h2 className="text-zinc-400 text-sm font-medium uppercase tracking-wider">System Risk</h2>
            <div className="flex items-end justify-between">
              <span className="text-3xl font-bold text-red-500">ELEVATED</span>
              <span className="text-2xl">📈</span>
            </div>
          </div>

          {/* AI Confidence Box */}
          <div className="md:col-span-1 md:row-span-1 border border-zinc-800 bg-zinc-950 p-6 rounded-3xl flex flex-col justify-between">
            <h2 className="text-zinc-400 text-sm font-medium uppercase tracking-wider">AI Confidence</h2>
            <div className="flex items-end justify-between">
              <span className="text-4xl font-bold">92%</span>
              <span className="text-2xl text-blue-500">🎯</span>
            </div>
          </div>

          {/* Predictive Analysis */}
          <div className="md:col-span-1 md:row-span-2 border border-zinc-800 bg-zinc-950 p-6 rounded-3xl">
            <h2 className="text-zinc-400 text-sm font-medium uppercase tracking-wider mb-4">Predictive Analysis</h2>
            <div className="space-y-4">
              <div className="h-2 w-full bg-zinc-900 rounded-full overflow-hidden">
                <div className="h-full bg-green-500 w-[70%]"></div>
              </div>
              <p className="text-xs text-zinc-500 font-mono">Initializing Neural Engine...</p>
            </div>
          </div>

          {/* AI News Analyst (The one we'll link to the JSON) */}
          <div className="md:col-span-3 md:row-span-1 border border-zinc-800 bg-zinc-950 p-6 rounded-3xl">
            <h2 className="text-zinc-400 text-sm font-medium uppercase tracking-wider mb-2">AI News Analyst</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-green-500 text-xs font-bold uppercase">Bullish Sense</p>
                <p className="text-sm text-zinc-300">Fed Rate hold confirmed...</p>
              </div>
              <div>
                <p className="text-red-500 text-xs font-bold uppercase">Bearish Sense</p>
                <p className="text-sm text-zinc-300">Crude Oil inventory spike...</p>
              </div>
            </div>
          </div>
        </div>
      </main>
  );
}