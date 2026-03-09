import data from "@/data/dashboard_data.json";

export default function AssetManagerDashboard() {
  return (
      <div className="flex min-h-screen bg-[#050505] text-zinc-200 font-sans selection:bg-blue-500/30">

        {/* SIDEBAR */}
        <aside className="w-20 lg:w-64 border-r border-zinc-900 bg-[#080808] p-6 flex flex-col gap-10">
          <div className="text-2xl font-black tracking-tighter text-white">FT <span className="text-[10px] text-blue-500 border border-blue-500 px-1 ml-1">PRO</span></div>
          <nav className="space-y-6 text-sm font-medium text-zinc-500">
            <div className="text-blue-500 cursor-pointer">Dashboard</div>
            <div className="hover:text-zinc-300 cursor-pointer">Portfolio</div>
            <div className="hover:text-zinc-300 cursor-pointer">Reports</div>
          </nav>
        </aside>

        {/* MAIN TERMINAL */}
        <main className="flex-1 p-8 overflow-y-auto">

          {/* HEADER */}
          <div className="flex justify-between items-end mb-10 border-b border-zinc-900 pb-6">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-white">HOME SCREEN</h1>
              <p className="text-zinc-500 text-xs font-mono uppercase tracking-widest mt-1">Asset Manager Dashboard // Ver 4.0.1</p>
            </div>
            <div className="text-right font-mono text-[10px] text-zinc-600">
              SYSTEM_STATUS: <span className="text-green-500">OPTIMAL</span><br/>
              LAST_SYNC: 10:42:01
            </div>
          </div>

          {/* BENTO GRID */}
          <div className="grid grid-cols-12 gap-5 auto-rows-[160px]">

            {/* 1. TOP MACRO THEMES (Wide Top) */}
            <section className="col-span-12 lg:col-span-8 row-span-1 bg-zinc-900/20 border border-zinc-800 rounded-2xl p-6 flex flex-col justify-center">
              <h2 className="text-zinc-500 text-[10px] uppercase tracking-[0.2em] mb-4">Top Macro-Economic Themes</h2>
              <div className="flex flex-wrap gap-3">
                {data.themes.map((theme) => (
                    <span key={theme} className="px-4 py-2 bg-zinc-900 border border-zinc-700 rounded-full text-xs font-medium hover:border-blue-500 transition-colors cursor-default">
                  # {theme}
                </span>
                ))}
              </div>
            </section>

            {/* 2. DAILY MACRO BRIEFING (Square-ish) */}
            <section className="col-span-12 lg:col-span-4 row-span-2 bg-blue-600 p-6 rounded-2xl text-white relative overflow-hidden group">
              <h2 className="text-blue-200 text-[10px] uppercase tracking-[0.2em] mb-4">Daily Macro Briefing</h2>
              <p className="text-lg font-bold leading-tight mb-4">{data.briefing}</p>
              <div className="absolute bottom-4 left-6 text-[10px] font-black underline cursor-pointer hover:text-black">READ FULL ANALYSIS →</div>
              <div className="absolute -right-4 -bottom-4 text-8xl opacity-10 font-black group-hover:scale-110 transition-transform">AI</div>
            </section>

            {/* 3. THEME HEATMAP (The Grid of data) */}
            <section className="col-span-12 lg:col-span-5 row-span-2 bg-zinc-900/20 border border-zinc-800 rounded-2xl p-6">
              <h2 className="text-zinc-500 text-[10px] uppercase tracking-[0.2em] mb-6">Theme Heatmap</h2>
              <div className="grid grid-cols-2 gap-4">
                {data.heatmap.map((item) => (
                    <div key={item.label} className="p-4 bg-zinc-950 rounded-xl border border-zinc-800 flex justify-between items-center">
                      <span className="text-sm font-mono text-zinc-400">{item.label}</span>
                      <span className={`text-xl font-bold ${item.status === 'pos' ? 'text-green-500' : 'text-red-500'}`}>
                    {item.status === 'pos' ? '+' : '-'}{item.value}%
                  </span>
                    </div>
                ))}
              </div>
            </section>

            {/* 4. SCENARIO STRESS TEST (Centered focus) */}
            <section className="col-span-12 lg:col-span-3 row-span-2 bg-zinc-950 border-2 border-dashed border-zinc-800 rounded-2xl p-6 flex flex-col justify-center items-center text-center">
              <h2 className="text-zinc-500 text-[10px] uppercase tracking-[0.2em] mb-4">Stress Test Results</h2>
              <div className="text-red-500 text-4xl font-black mb-2">{data.stress_test.probability}</div>
              <p className="text-sm font-bold text-white mb-1 uppercase">{data.stress_test.scenario}</p>
              <p className="text-[10px] text-zinc-600 font-mono">Impact: {data.stress_test.impact}</p>
            </section>

            {/* 5. RECENT MACRO EVENTS (Ticker style) */}
            <section className="col-span-12 lg:col-span-12 row-span-1 bg-zinc-900/10 border border-zinc-900 rounded-2xl p-6 flex items-center overflow-hidden">
              <div className="text-zinc-500 text-[10px] uppercase tracking-[0.2em] mr-8 whitespace-nowrap">Recent Events</div>
              <div className="flex gap-10">
                {data.events.map((event, i) => (
                    <div key={i} className="flex items-center gap-3 whitespace-nowrap">
                      <span className="text-blue-500 font-mono text-xs">{event.time}</span>
                      <span className="text-sm font-bold">{event.title}</span>
                      <span className="px-2 py-0.5 bg-zinc-800 text-[8px] rounded uppercase">{event.impact}</span>
                    </div>
                ))}
              </div>
            </section>

          </div>
        </main>
      </div>
  );
}