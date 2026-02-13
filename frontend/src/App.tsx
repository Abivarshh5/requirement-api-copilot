import { useState, useRef } from 'react';
import type { SpecOutput, TabId, GenerateResponse } from './types';
import { generateSpec, refineSpec } from './api';
import InputPanel from './components/InputPanel';
import TabNav from './components/TabNav';
import ModulesTab from './components/ModulesTab';
import UserStoriesTab from './components/UserStoriesTab';
import ApiEndpointsTab from './components/ApiEndpointsTab';
import DatabaseTab from './components/DatabaseTab';
import IssuesTab from './components/IssuesTab';
import ExportPanel from './components/ExportPanel';
import RefineModal from './components/RefineModal';

function App() {
  const [requirements, setRequirements] = useState('');
  const [spec, setSpec] = useState<SpecOutput | null>(null);
  const [traceId, setTraceId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<TabId>('modules');
  const [isLoading, setIsLoading] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [showRefineModal, setShowRefineModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [progressStep, setProgressStep] = useState('');

  const outputRef = useRef<HTMLDivElement>(null);

  const handleGenerate = async () => {
    setError(null);
    setIsLoading(true);
    setProgressStep('Analyzing requirements...');
    setSpec(null);
    setWarnings([]);

    try {
      const stepMessages = [
        'Extracting modules & features...',
        'Generating user stories...',
        'Designing APIs & database...',
      ];
      let stepIdx = 0;
      const interval = setInterval(() => {
        stepIdx = Math.min(stepIdx + 1, stepMessages.length - 1);
        setProgressStep(stepMessages[stepIdx]);
      }, 4000);

      const result: GenerateResponse = await generateSpec(requirements);

      clearInterval(interval);
      setSpec(result.spec);
      setTraceId(result.trace_id);
      setWarnings(result.warnings || []);
      setActiveTab('modules');

      // Scroll to output
      setTimeout(() => {
        outputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err: any) {
      const msg = err?.message || 'Failed to generate specification';
      const details = err?.details;
      if (details?.suggestions) {
        setError(`${msg}. Try: ${details.suggestions.join(', ')}`);
      } else {
        setError(msg);
      }
    } finally {
      setIsLoading(false);
      setProgressStep('');
    }
  };

  const handleRefine = async (instructions: string) => {
    if (!spec) return;
    setIsRefining(true);
    setError(null);

    try {
      const result = await refineSpec(traceId, spec as unknown as Record<string, unknown>, instructions);
      setSpec(result.spec);
      setTraceId(result.trace_id);
      setShowRefineModal(false);
    } catch (err: any) {
      setError(err?.message || 'Refinement failed');
    } finally {
      setIsRefining(false);
    }
  };

  const tabCounts: Record<TabId, number> = spec
    ? {
      modules: spec.modules.length,
      stories: spec.user_stories.length,
      endpoints: spec.api_endpoints.length,
      database: spec.db_schema.length,
      issues: spec.open_questions.length + spec.contradictions.length,
    }
    : { modules: 0, stories: 0, endpoints: 0, database: 0, issues: 0 };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 glass border-b border-surface-200/5" style={{ borderRadius: 0 }}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg shadow-brand-500/25">
              <span className="text-white text-lg font-bold">⚙</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                Requirement → API Copilot
              </h1>
              <p className="text-[11px] text-surface-200/40">Transform requirements into specs with AI</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener"
              className="btn-ghost text-xs"
            >
              GitHub
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Input Section */}
        <InputPanel
          value={requirements}
          onChange={setRequirements}
          onGenerate={handleGenerate}
          isLoading={isLoading}
          error={error}
        />

        {/* Loading Progress */}
        {isLoading && (
          <div className="glass p-8 text-center animate-fade-in">
            <div className="flex flex-col items-center gap-4">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 rounded-full border-2 border-brand-500/20"></div>
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-brand-500 animate-spin"></div>
                <div className="absolute inset-3 rounded-full bg-gradient-to-br from-brand-500/20 to-purple-500/20 animate-pulse-slow"></div>
              </div>
              <div>
                <p className="text-sm font-medium text-white">{progressStep}</p>
                <p className="text-xs text-surface-200/40 mt-1">This may take 15-30 seconds with a real LLM</p>
              </div>
            </div>
          </div>
        )}

        {/* Warnings */}
        {warnings.length > 0 && (
          <div className="px-4 py-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-amber-300 text-sm flex items-start gap-2 animate-fade-in">
            <span>⚠️</span>
            <div>
              {warnings.map((w, i) => (
                <p key={i}>{w}</p>
              ))}
            </div>
          </div>
        )}

        {/* Output Section */}
        {spec && !isLoading && (
          <div ref={outputRef} className="space-y-4 animate-slide-up">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                <span className="text-white text-sm">📊</span>
              </div>
              <h2 className="text-lg font-semibold text-white">Generated Specification</h2>
            </div>

            <TabNav activeTab={activeTab} onTabChange={setActiveTab} counts={tabCounts} />

            <div className="glass p-5 min-h-[300px]">
              {activeTab === 'modules' && (
                <ModulesTab modules={spec.modules} featuresByModule={spec.features_by_module} />
              )}
              {activeTab === 'stories' && (
                <UserStoriesTab stories={spec.user_stories} modules={spec.modules} />
              )}
              {activeTab === 'endpoints' && (
                <ApiEndpointsTab endpoints={spec.api_endpoints} />
              )}
              {activeTab === 'database' && (
                <DatabaseTab tables={spec.db_schema} />
              )}
              {activeTab === 'issues' && (
                <IssuesTab questions={spec.open_questions} contradictions={spec.contradictions} />
              )}
            </div>

            <ExportPanel spec={spec} onRefine={() => setShowRefineModal(true)} />
          </div>
        )}

        {/* Empty State */}
        {!spec && !isLoading && (
          <div className="glass p-12 text-center animate-fade-in">
            <div className="max-w-md mx-auto">
              <div className="text-5xl mb-4">🚀</div>
              <h3 className="text-xl font-semibold text-white mb-2">Ready to analyze</h3>
              <p className="text-sm text-surface-200/50 mb-6">
                Paste your product requirements above and click "Generate Specification" to transform them into structured technical specs.
              </p>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 rounded-xl bg-surface-800/30">
                  <div className="text-2xl mb-1">📦</div>
                  <p className="text-[11px] text-surface-200/50">Modules & Features</p>
                </div>
                <div className="p-3 rounded-xl bg-surface-800/30">
                  <div className="text-2xl mb-1">🔌</div>
                  <p className="text-[11px] text-surface-200/50">API Endpoints</p>
                </div>
                <div className="p-3 rounded-xl bg-surface-800/30">
                  <div className="text-2xl mb-1">🗄️</div>
                  <p className="text-[11px] text-surface-200/50">Database Schema</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-4 sm:px-6 py-8 text-center text-xs text-surface-200/30">
        <p>Requirement → API Copilot v1.0.0 • Powered by Google Gemini 2.0</p>
      </footer>

      {/* Refine Modal */}
      <RefineModal
        isOpen={showRefineModal}
        onClose={() => setShowRefineModal(false)}
        onSubmit={handleRefine}
        isLoading={isRefining}
      />
    </div>
  );
}

export default App;
