import React from 'react';

function App() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Disclaimer Banner - AGENTS.md Non-Negotiable */}
      <div className="bg-amber-500 text-amber-950 px-4 py-2 text-xs font-medium text-center border-b border-amber-600/20">
        ⚠️ <strong>Notice</strong>: LegalLens is an automated first-pass contract analysis tool. It does not provide legal advice and is not a substitute for a qualified attorney.
      </div>

      <header className="bg-white border-b border-slate-200 px-6 py-4 shadow-sm flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-lg">
            ⚖️
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">LegalLens</h1>
            <p className="text-xs text-slate-500">AI-Powered Contract Intelligence Platform</p>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-slate-800">Welcome to LegalLens</h2>
          <p className="text-slate-600 mt-2">Document upload and analysis pipeline will appear here.</p>
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 px-6 text-center text-xs text-slate-500">
        LegalLens MCA Mini Project &bull; Strictly for academic & first-pass evaluation purposes.
      </footer>
    </div>
  );
}

export default App;
