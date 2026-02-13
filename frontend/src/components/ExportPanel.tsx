import React, { useState } from 'react';
import type { SpecOutput } from '../types';

interface ExportPanelProps {
    spec: SpecOutput;
    onRefine: () => void;
}

const ExportPanel: React.FC<ExportPanelProps> = ({ spec, onRefine }) => {
    const [copied, setCopied] = useState(false);
    const [copiedTraceId, setCopiedTraceId] = useState(false);

    const downloadJSON = () => {
        const json = JSON.stringify(spec, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        a.href = url;
        a.download = `spec_${spec.trace_id.slice(0, 8)}_${ts}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const copyJSON = async () => {
        const json = JSON.stringify(spec, null, 2);
        await navigator.clipboard.writeText(json);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const copyTraceId = async () => {
        await navigator.clipboard.writeText(spec.trace_id);
        setCopiedTraceId(true);
        setTimeout(() => setCopiedTraceId(false), 2000);
    };

    const timeAgo = () => {
        const diff = Date.now() - new Date(spec.timestamp).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return 'just now';
        if (mins === 1) return '1 min ago';
        if (mins < 60) return `${mins} mins ago`;
        const hrs = Math.floor(mins / 60);
        return `${hrs}h ago`;
    };

    return (
        <div className="glass p-5 animate-fade-in">
            <div className="flex flex-wrap items-center gap-3">
                <button onClick={downloadJSON} className="btn-secondary flex items-center gap-2">
                    <span>💾</span> Download JSON
                </button>
                <button onClick={copyJSON} className="btn-secondary flex items-center gap-2">
                    <span>{copied ? '✅' : '📋'}</span> {copied ? 'Copied!' : 'Copy JSON'}
                </button>
                <button onClick={onRefine} className="btn-primary flex items-center gap-2">
                    <span>🔄</span> Refine Spec
                </button>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-surface-200/40">
                <button onClick={copyTraceId} className="flex items-center gap-1 hover:text-surface-200/60 transition-colors" title="Click to copy">
                    <span className="font-mono">Trace: {spec.trace_id.slice(0, 8)}...</span>
                    {copiedTraceId && <span className="text-emerald-400">copied!</span>}
                </button>
                <span>v{spec.version}</span>
                <span>Generated {timeAgo()}</span>
                <span>•</span>
                <span>{spec.metadata.processing_time_ms}ms</span>
                <span>•</span>
                <span>{spec.metadata.llm_model}</span>
            </div>
        </div>
    );
};

export default ExportPanel;
