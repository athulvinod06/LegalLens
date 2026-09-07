import React, { useState, useRef } from 'react';
import {
  ShieldAlert, ShieldCheck, AlertTriangle, FileText, UploadCloud,
  Send, Download, CheckCircle2, XCircle, MessageSquare, Search,
  Info, ExternalLink, Sparkles, RefreshCw
} from 'lucide-react';

const CONTRACT_TYPES = [
  { id: 'freelance', label: 'Freelance Agreement' },
  { id: 'employment', label: 'Employment Agreement' },
  { id: 'rental', label: 'Residential Lease / Rental' },
  { id: 'vendor', label: 'Vendor Procurement' },
];

export default function App() {
  const [selectedType, setSelectedType] = useState('freelance');
  const [file, setFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);

  // Clause filtering
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [onlyFlagged, setOnlyFlagged] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedClauseId, setHighlightedClauseId] = useState(null);

  // Chat state
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'Hello! I am LegalLens AI. Ask me any clause-specific question about this contract and I will provide an answer grounded strictly in the text with citations.',
      citations: [],
      isGrounded: true
    }
  ]);
  const [questionInput, setQuestionInput] = useState('');
  const [isAsking, setIsAsking] = useState(false);

  const fileInputRef = useRef(null);
  const clauseRefs = useRef({});

  // Quick sample loader
  const handleLoadSample = async (type) => {
    setSelectedType(type);
    setIsAnalyzing(true);
    setError(null);
    try {
      const resp = await fetch(`/api/documents/sample/${type}`, { method: 'POST' });
      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || 'Failed to load sample contract');
      }
      const data = await resp.json();
      setAnalysis(data);
      setMessages([
        {
          sender: 'bot',
          text: `Loaded ${type} contract (${data.filename}). You can now explore the risk breakdown or ask grounded questions below.`,
          citations: [],
          isGrounded: true
        }
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Upload handler
  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files?.[0] || file;
    if (!uploadedFile) return;

    setIsAnalyzing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', uploadedFile);
    formData.append('contract_type', selectedType);
    formData.append('user_id', 'demo_user');

    try {
      const resp = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || 'Failed to analyze contract');
      }

      const data = await resp.json();
      setAnalysis(data);
      setMessages([
        {
          sender: 'bot',
          text: `Analysis complete for ${data.filename}. Ask any question about its terms, liabilities, or termination rights.`,
          citations: [],
          isGrounded: true
        }
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Chat submit
  const handleAskQuestion = async (e) => {
    e?.preventDefault();
    if (!questionInput.trim() || !analysis || isAsking) return;

    const userQ = questionInput.trim();
    setQuestionInput('');
    setMessages(prev => [...prev, { sender: 'user', text: userQ }]);
    setIsAsking(true);

    try {
      const resp = await fetch('/api/documents/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contract_id: analysis.contract_id,
          question: userQ,
          user_id: 'demo_user'
        })
      });

      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.detail || 'Failed to process question');
      }

      const data = await resp.json();
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: data.answer,
          citations: data.citations || [],
          isGrounded: data.is_grounded
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: `Error: ${err.message}`,
          citations: [],
          isGrounded: false
        }
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  // PDF Export
  const handleExportPDF = async () => {
    if (!analysis) return;
    try {
      const resp = await fetch('/api/documents/export-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(analysis)
      });
      if (!resp.ok) throw new Error('PDF export failed');
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `LegalLens_${analysis.filename.replace(/\.[^/.]+$/, "")}_Audit.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert(`Could not export PDF: ${err.message}`);
    }
  };

  const scrollToClause = (cid) => {
    setHighlightedClauseId(cid);
    const elem = clauseRefs.current[cid];
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Derived filtered clauses
  const filteredClauses = (analysis?.clauses || []).filter(c => {
    if (categoryFilter !== 'ALL' && c.category !== categoryFilter) return false;
    const clauseFlag = (analysis?.risk_report?.flags || []).find(f => f.clause_id === c.clause_id);
    if (onlyFlagged && !clauseFlag) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const inText = c.text.toLowerCase().includes(q);
      const inTitle = (c.title || '').toLowerCase().includes(q);
      const inCat = c.category.toLowerCase().includes(q);
      if (!inText && !inTitle && !inCat) return false;
    }
    return true;
  });

  const overallScore = analysis?.risk_report?.overall_score ?? 100;
  const riskLevel = analysis?.risk_report?.risk_level ?? 'Low Risk';
  const flags = analysis?.risk_report?.flags ?? [];
  const omissions = analysis?.risk_report?.omissions ?? [];

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col font-sans">
      {/* 1. Mandatory Constitutional Legal Disclaimer */}
      <aside aria-label="Legal Disclaimer" className="bg-amber-500 text-amber-950 px-4 py-2 text-xs font-semibold text-center border-b border-amber-600/30 flex items-center justify-center gap-2 shadow-sm">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>LEGAL DISCLAIMER:</strong> LegalLens is an automated first-pass contract analysis tool. It highlights potential risks and provides clause-grounded explanations. It does NOT provide legal advice and is not a substitute for a licensed lawyer.
        </span>
      </aside>

      {/* 2. Main Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white flex items-center justify-center text-xl shadow-sm">
              ⚖️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">LegalLens</h1>
              </div>
              <p className="text-xs text-slate-500">AI-Powered Explainable Contract Intelligence</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {analysis && (
              <button
                onClick={handleExportPDF}
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition shadow-sm"
              >
                <Download className="h-3.5 w-3.5 text-blue-600" />
                Export PDF Audit
              </button>
            )}
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 transition"
            >
              API Docs <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </header>

      {/* 3. Main Dashboard Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col gap-6">
        
        {/* Upload & Demo Selector Card */}
        <section className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900">Upload or Select a Contract</h2>
              <p className="text-xs text-slate-500 mt-0.5">Supports PDF and DOCX files. Preserves section hierarchy and checks essential checklists.</p>
            </div>

            {/* Contract Type Dropdown */}
            <div className="flex items-center gap-2">
              <label htmlFor="contract-type-select" className="text-xs font-medium text-slate-600">Contract Type:</label>
              <select
                id="contract-type-select"
                aria-label="Contract Type"
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="text-xs font-semibold bg-slate-50 border border-slate-300 text-slate-800 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {CONTRACT_TYPES.map(t => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Quick Demo Pre-load Buttons */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
              <Sparkles className="h-3.5 w-3.5 text-amber-500" /> Quick Samples:
            </span>
            {CONTRACT_TYPES.map(t => (
              <button
                key={t.id}
                onClick={() => handleLoadSample(t.id)}
                disabled={isAnalyzing}
                className="text-xs px-2.5 py-1 rounded-md bg-slate-100 hover:bg-blue-50 hover:text-blue-700 text-slate-700 font-medium transition border border-slate-200/80 disabled:opacity-50"
              >
                Sample {t.label.split(' ')[0]}
              </button>
            ))}
          </div>

          {/* Drag and drop upload box */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="mt-4 border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer bg-slate-50/60 hover:bg-blue-50/30 transition flex flex-col items-center justify-center gap-2"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.docx"
              className="hidden"
            />
            <div className="h-12 w-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
              <UploadCloud className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">
                {file ? file.name : "Click or drag & drop contract here"}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">PDF or DOCX (digital text only, up to 20 pages)</p>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
              <XCircle className="h-4 w-4 shrink-0 text-red-500" />
              <span>{error}</span>
            </div>
          )}

          {/* Loading Spinner */}
          {isAnalyzing && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-center gap-3 text-xs text-blue-800 font-medium animate-pulse">
              <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
              <span>Extracting text &bull; Segmenting clauses &bull; InLegalBERT CUAD Classification &bull; Calculating Risk Deductions...</span>
            </div>
          )}
        </section>

        {/* 4. Analysis Results Dashboard (If analyzed) */}
        {analysis && (
          <div className="flex flex-col gap-6">
            
            {/* Executive Risk Score Gauge Card */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              
              {/* Overall Score */}
              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center gap-4">
                <div className={`h-16 w-16 rounded-2xl flex flex-col items-center justify-center font-bold shadow-inner ${
                  overallScore >= 80 ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' :
                  overallScore >= 50 ? 'bg-amber-50 text-amber-600 border border-amber-200' :
                  'bg-rose-50 text-rose-600 border border-rose-200'
                }`}>
                  <span className="text-2xl leading-none">{overallScore}</span>
                  <span className="text-[10px] uppercase font-semibold text-slate-400">/100</span>
                </div>
                <div>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                    overallScore >= 80 ? 'bg-emerald-100 text-emerald-800' :
                    overallScore >= 50 ? 'bg-amber-100 text-amber-800' :
                    'bg-rose-100 text-rose-800'
                  }`}>
                    {riskLevel}
                  </span>
                  <p className="text-xs text-slate-500 mt-1">
                    Weighted-Deduction Score
                  </p>
                </div>
              </div>

              {/* Deductions Stat */}
              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Deductions</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">-{analysis.risk_report.total_deductions} pts</p>
                <p className="text-xs text-slate-500 mt-1">Sum of weighted penalties</p>
              </div>

              {/* Flagged Clauses Stat */}
              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Flagged Risk Issues</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{flags.length}</p>
                <p className="text-xs text-slate-500 mt-1">Traceable to heuristic rules</p>
              </div>

              {/* Total Clauses Stat */}
              <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Clauses Analyzed</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{analysis.clauses.length}</p>
                <p className="text-xs text-slate-500 mt-1">InLegalBERT 15-core classes</p>
              </div>
            </div>

            {/* Missing Essential Clauses Alert */}
            {omissions.length > 0 && (
              <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start gap-3">
                <ShieldAlert className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wider">
                    Missing Essential Protective Clauses ({omissions.length})
                  </h4>
                  <p className="text-xs text-rose-700 mt-1">
                    This {analysis.contract_type} contract lacks standard provisions for: <strong>{omissions.map(o => o.replace('_', ' ')).join(', ')}</strong>. Consider negotiating to insert clear mutual provisions for these areas.
                  </p>
                </div>
              </div>
            )}

            {/* Split View: Clauses Explorer (Left 7 cols) & Grounded Q&A Chat (Right 5 cols) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              
              {/* Left Column: Clause-by-Clause Explorer */}
              <div className="lg:col-span-7 flex flex-col gap-4">
                <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
                  
                  {/* Search and Filters */}
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pb-4 border-b border-slate-100">
                    <div className="relative w-full sm:w-64">
                      <Search className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-2.5" />
                      <input
                        type="text"
                        placeholder="Search clauses..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>

                    <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                      <select
                        aria-label="Filter by Category"
                        value={categoryFilter}
                        onChange={(e) => setCategoryFilter(e.target.value)}
                        className="text-xs bg-slate-50 border border-slate-200 text-slate-700 rounded-lg px-2.5 py-1.5"
                      >
                        <option value="ALL">All Categories</option>
                        {Array.from(new Set(analysis.clauses.map(c => c.category))).map(cat => (
                          <option key={cat} value={cat}>{cat.replace('_', ' ')}</option>
                        ))}
                      </select>

                      <button
                        onClick={() => setOnlyFlagged(!onlyFlagged)}
                        className={`text-xs px-2.5 py-1.5 rounded-lg border font-medium transition ${
                          onlyFlagged
                            ? 'bg-rose-50 border-rose-300 text-rose-700'
                            : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                        }`}
                      >
                        Flagged Only
                      </button>
                    </div>
                  </div>

                  {/* Clauses List */}
                  <div className="mt-4 flex flex-col gap-3 max-h-[650px] overflow-y-auto pr-1">
                    {filteredClauses.map((clause) => {
                      const clauseFlag = flags.find(f => f.clause_id === clause.clause_id);
                      const isHighlighted = highlightedClauseId === clause.clause_id;

                      return (
                        <div
                          key={clause.clause_id}
                          ref={el => clauseRefs.current[clause.clause_id] = el}
                          className={`rounded-xl p-4 border transition ${
                            isHighlighted
                              ? 'ring-2 ring-blue-600 bg-blue-50/40 border-blue-300'
                              : clauseFlag
                              ? 'bg-rose-50/20 border-rose-200'
                              : 'bg-white border-slate-200 hover:border-slate-300'
                          }`}
                        >
                          {/* Clause Header */}
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-slate-700">
                                {clause.clause_number || `Clause ${clause.clause_id}`}
                              </span>
                              {clause.title && (
                                <span className="text-xs font-semibold text-slate-900">
                                  &bull; {clause.title}
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="text-[10px] bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded-md">
                                {clause.category.replace('_', ' ')} ({Math.round(clause.confidence * 100)}%)
                              </span>
                              {clauseFlag && (
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                                  clauseFlag.severity === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                                  clauseFlag.severity === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                                  'bg-slate-100 text-slate-800'
                                }`}>
                                  -{clauseFlag.deduction_points} pts
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Clause Text */}
                          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                            {clause.text}
                          </p>

                          {/* Flag Traceability Breakdown */}
                          {clauseFlag && (
                            <div className="mt-3 p-3 bg-rose-50/70 border border-rose-200/80 rounded-lg text-xs">
                              <div className="flex items-center gap-1.5 text-rose-900 font-bold">
                                <AlertTriangle className="h-3.5 w-3.5 text-rose-600" />
                                <span>{clauseFlag.rule_name}</span>
                                <span className="text-[10px] text-rose-600 font-mono">({clauseFlag.rule_id})</span>
                              </div>
                              <p className="text-slate-700 mt-1">{clauseFlag.explanation}</p>
                              <p className="text-slate-600 font-medium mt-1">
                                <strong>Recommended Remedy:</strong> {clauseFlag.recommendation}
                              </p>
                            </div>
                          )}
                        </div>
                      );
                    })}

                    {filteredClauses.length === 0 && (
                      <p className="text-center py-8 text-xs text-slate-400">
                        No clauses match your filter criteria.
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column: Conversational Grounded RAG Chat Panel */}
              <div className="lg:col-span-5 flex flex-col">
                <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col h-[740px]">
                  
                  {/* Chat Header */}
                  <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 rounded-t-2xl">
                    <div className="flex items-center gap-2">
                      <div className="h-7 w-7 rounded-lg bg-blue-600 text-white flex items-center justify-center">
                        <MessageSquare className="h-4 w-4" />
                      </div>
                      <div>
                        <h3 className="text-xs font-bold text-slate-900">Grounded Contract Q&A</h3>
                        <p className="text-[10px] text-slate-500">Retrieves source clauses &bull; Strict anti-hallucination</p>
                      </div>
                    </div>
                  </div>

                  {/* Chat Messages Feed */}
                  <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3">
                    {messages.map((m, idx) => (
                      <div
                        key={idx}
                        className={`flex flex-col max-w-[88%] ${
                          m.sender === 'user' ? 'self-end items-end' : 'self-start items-start'
                        }`}
                      >
                        <div
                          className={`p-3 rounded-2xl text-xs leading-relaxed ${
                            m.sender === 'user'
                              ? 'bg-blue-600 text-white rounded-tr-none'
                              : 'bg-slate-100 text-slate-800 rounded-tl-none border border-slate-200'
                          }`}
                        >
                          <p>{m.text}</p>

                          {/* Clickable Citations */}
                          {m.citations && m.citations.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-slate-200/60 flex flex-wrap items-center gap-1.5">
                              <span className="text-[10px] text-slate-500 font-semibold">Citations:</span>
                              {m.citations.map(cid => (
                                <button
                                  key={cid}
                                  onClick={() => scrollToClause(cid)}
                                  className="text-[10px] bg-blue-100 hover:bg-blue-200 text-blue-800 font-bold px-1.5 py-0.5 rounded transition"
                                >
                                  Clause {cid}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}

                    {isAsking && (
                      <div className="self-start bg-slate-100 text-slate-500 text-xs p-3 rounded-2xl rounded-tl-none border border-slate-200 animate-pulse">
                        Retrieving relevant clauses & synthesizing grounded answer...
                      </div>
                    )}
                  </div>

                  {/* Quick Suggested Prompts */}
                  <div className="px-4 py-2 border-t border-slate-100 bg-slate-50/70 flex flex-wrap gap-1.5">
                    {[
                      "How can this agreement be terminated?",
                      "What are the payment terms and fees?",
                      "Is there an uncapped liability clause?",
                      "Are there pet restrictions?"
                    ].map((promptText, i) => (
                      <button
                        key={i}
                        onClick={() => setQuestionInput(promptText)}
                        className="text-[10px] bg-white border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-300 rounded px-2 py-0.5 transition"
                      >
                        {promptText}
                      </button>
                    ))}
                  </div>

                  {/* Chat Input Box */}
                  <form onSubmit={handleAskQuestion} className="p-3 border-t border-slate-200 flex items-center gap-2">
                    <input
                      type="text"
                      placeholder="Ask any question about this contract..."
                      value={questionInput}
                      onChange={(e) => setQuestionInput(e.target.value)}
                      disabled={isAsking}
                      className="flex-1 text-xs bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      type="submit"
                      disabled={isAsking || !questionInput.trim()}
                      className="h-9 w-9 rounded-xl bg-blue-600 text-white flex items-center justify-center hover:bg-blue-700 disabled:opacity-50 transition shrink-0"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 px-6 text-center text-xs text-slate-500">
        LegalLens
      </footer>
    </div>
  );
}
