import React, { useState } from 'react';
import type { ApiEndpoint } from '../types';

interface ApiEndpointsTabProps {
    endpoints: ApiEndpoint[];
}

const methodBadgeClass: Record<string, string> = {
    GET: 'badge-method-get',
    POST: 'badge-method-post',
    PUT: 'badge-method-put',
    PATCH: 'badge-method-patch',
    DELETE: 'badge-method-delete',
};

const ApiEndpointsTab: React.FC<ApiEndpointsTabProps> = ({ endpoints }) => {
    const [expanded, setExpanded] = useState<Set<string>>(new Set());

    const toggle = (id: string) => {
        setExpanded(prev => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    };

    const copyAsCurl = (ep: ApiEndpoint) => {
        let curl = `curl -X ${ep.method} '${ep.path}'`;
        if (ep.request?.headers) {
            Object.entries(ep.request.headers).forEach(([k, v]) => {
                curl += ` \\\n  -H '${k}: ${v}'`;
            });
        }
        if (ep.request?.body) {
            curl += ` \\\n  -H 'Content-Type: application/json' \\\n  -d '${JSON.stringify(ep.request.body, null, 2)}'`;
        }
        navigator.clipboard.writeText(curl);
    };

    if (endpoints.length === 0) {
        return (
            <div className="text-center py-10 text-surface-200/40">
                <p className="text-4xl mb-3">🔌</p>
                <p>No API endpoints generated yet.</p>
            </div>
        );
    }

    // Group by resource path prefix
    const grouped: Record<string, ApiEndpoint[]> = {};
    endpoints.forEach(ep => {
        const parts = ep.path.split('/').filter(Boolean);
        const resource = parts.length > 1 ? `/${parts[0]}/${parts[1]}` : ep.path;
        if (!grouped[resource]) grouped[resource] = [];
        grouped[resource].push(ep);
    });

    return (
        <div className="space-y-4 animate-fade-in">
            {Object.entries(grouped).map(([resource, eps]) => (
                <div key={resource} className="glass-sm overflow-hidden">
                    <div className="px-5 py-3 border-b border-surface-200/5">
                        <h3 className="text-xs font-mono text-surface-200/50 uppercase tracking-wider">{resource}</h3>
                    </div>
                    <div className="divide-y divide-surface-200/5">
                        {eps.map(ep => {
                            const isOpen = expanded.has(ep.endpoint_id);
                            return (
                                <div key={ep.endpoint_id}>
                                    <button
                                        onClick={() => toggle(ep.endpoint_id)}
                                        className="w-full flex items-center gap-3 px-5 py-3 hover:bg-surface-700/20 transition-colors"
                                    >
                                        <span className={`badge ${methodBadgeClass[ep.method]}`}>{ep.method}</span>
                                        <span className="font-mono text-sm text-surface-50 flex-1 text-left">
                                            {ep.path.split('/').map((part, i) => (
                                                <React.Fragment key={i}>
                                                    {i > 0 && <span className="text-surface-200/30">/</span>}
                                                    {part.startsWith('{') ? (
                                                        <span className="text-amber-400">{part}</span>
                                                    ) : (
                                                        <span>{part}</span>
                                                    )}
                                                </React.Fragment>
                                            ))}
                                        </span>
                                        <span className="text-xs text-surface-200/40 hidden md:block max-w-[200px] truncate">{ep.description}</span>
                                        {ep.authentication === 'required' && (
                                            <span className="text-amber-400 text-xs" title="Authentication required">🔒</span>
                                        )}
                                        <span className={`text-xs transition-transform ${isOpen ? 'rotate-180' : ''}`}>▼</span>
                                    </button>

                                    {isOpen && (
                                        <div className="px-5 py-4 bg-surface-800/30 space-y-4 animate-slide-up">
                                            <div className="flex items-center justify-between">
                                                <p className="text-sm text-surface-200/70">{ep.description}</p>
                                                <button
                                                    onClick={() => copyAsCurl(ep)}
                                                    className="btn-ghost text-xs flex items-center gap-1"
                                                >
                                                    📋 Copy cURL
                                                </button>
                                            </div>

                                            <div className="flex gap-3 flex-wrap text-xs">
                                                <span className={`badge ${ep.authentication === 'required' ? 'badge-high' : ep.authentication === 'optional' ? 'badge-medium' : 'badge-low'}`}>
                                                    Auth: {ep.authentication}
                                                </span>
                                                {ep.authorization && (
                                                    <span className="badge bg-purple-500/15 text-purple-300 border border-purple-500/20">
                                                        Role: {ep.authorization}
                                                    </span>
                                                )}
                                            </div>

                                            {/* Request */}
                                            {ep.request && (
                                                <div>
                                                    <h4 className="text-xs font-semibold text-surface-200/50 uppercase tracking-wider mb-2">Request</h4>
                                                    {ep.request.headers && Object.keys(ep.request.headers).length > 0 && (
                                                        <div className="mb-2">
                                                            <p className="text-[10px] text-surface-200/40 mb-1">Headers</p>
                                                            <pre className="text-xs bg-surface-900/50 rounded-lg p-3 overflow-x-auto font-mono text-emerald-300">
                                                                {JSON.stringify(ep.request.headers, null, 2)}
                                                            </pre>
                                                        </div>
                                                    )}
                                                    {ep.request.query_params && Object.keys(ep.request.query_params).length > 0 && (
                                                        <div className="mb-2">
                                                            <p className="text-[10px] text-surface-200/40 mb-1">Query Parameters</p>
                                                            <pre className="text-xs bg-surface-900/50 rounded-lg p-3 overflow-x-auto font-mono text-blue-300">
                                                                {JSON.stringify(ep.request.query_params, null, 2)}
                                                            </pre>
                                                        </div>
                                                    )}
                                                    {ep.request.body && (
                                                        <div>
                                                            <p className="text-[10px] text-surface-200/40 mb-1">Body</p>
                                                            <pre className="text-xs bg-surface-900/50 rounded-lg p-3 overflow-x-auto font-mono text-amber-300">
                                                                {JSON.stringify(ep.request.body, null, 2)}
                                                            </pre>
                                                        </div>
                                                    )}
                                                </div>
                                            )}

                                            {/* Response */}
                                            <div>
                                                <h4 className="text-xs font-semibold text-surface-200/50 uppercase tracking-wider mb-2">Response</h4>
                                                <div className="mb-2">
                                                    <p className="text-[10px] text-emerald-400 mb-1">✓ {ep.response.success.status_code} Success</p>
                                                    <pre className="text-xs bg-surface-900/50 rounded-lg p-3 overflow-x-auto font-mono text-emerald-300">
                                                        {JSON.stringify(ep.response.success.body, null, 2)}
                                                    </pre>
                                                </div>
                                                {ep.response.errors.length > 0 && (
                                                    <div className="space-y-2">
                                                        {ep.response.errors.map((err, i) => (
                                                            <div key={i}>
                                                                <p className="text-[10px] text-red-400 mb-1">✗ {err.status_code} {err.description}</p>
                                                                {err.body && (
                                                                    <pre className="text-xs bg-surface-900/50 rounded-lg p-3 overflow-x-auto font-mono text-red-300">
                                                                        {JSON.stringify(err.body, null, 2)}
                                                                    </pre>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>

                                            {ep.related_stories.length > 0 && (
                                                <div>
                                                    <p className="text-[10px] text-surface-200/40 mb-1">Related Stories</p>
                                                    <div className="flex gap-1 flex-wrap">
                                                        {ep.related_stories.map((sid) => (
                                                            <span key={sid} className="badge bg-brand-500/15 text-brand-300 border border-brand-500/20">{sid}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default ApiEndpointsTab;
