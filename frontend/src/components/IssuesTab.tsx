import React from 'react';
import type { OpenQuestion, Contradiction } from '../types';

interface IssuesTabProps {
    questions: OpenQuestion[];
    contradictions: Contradiction[];
}

const categoryIcon: Record<string, string> = {
    authentication: '🔐',
    business_logic: '💼',
    data_model: '📊',
    integration: '🔗',
    other: '📌',
};

const IssuesTab: React.FC<IssuesTabProps> = ({ questions, contradictions }) => {
    if (questions.length === 0 && contradictions.length === 0) {
        return (
            <div className="text-center py-10 text-surface-200/40">
                <p className="text-4xl mb-3">✅</p>
                <p>No open questions or contradictions found.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Open Questions */}
            {questions.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold text-surface-200/60 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <span>❓</span> Open Questions ({questions.length})
                    </h3>
                    <div className="space-y-2">
                        {questions.map((q) => (
                            <div key={q.question_id} className="glass-sm p-4 hover:border-brand-500/20 transition-colors">
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex items-start gap-3 flex-1">
                                        <span className="text-lg" title={q.category}>{categoryIcon[q.category] || '📌'}</span>
                                        <div>
                                            <p className="text-sm font-medium text-white">{q.question}</p>
                                            <p className="text-xs text-surface-200/40 mt-1">{q.context}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 flex-shrink-0">
                                        <span className={`badge ${q.priority === 'high' ? 'badge-high' : q.priority === 'medium' ? 'badge-medium' : 'badge-low'}`}>
                                            {q.priority}
                                        </span>
                                        <span className="badge bg-surface-700 text-surface-200/50 border-surface-200/10">
                                            {q.category.replace('_', ' ')}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Contradictions */}
            {contradictions.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold text-red-400/70 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <span>⚡</span> Contradictions ({contradictions.length})
                    </h3>
                    <div className="space-y-2">
                        {contradictions.map((c, i) => (
                            <div key={i} className="glass-sm p-4 border-red-500/20">
                                <p className="text-sm font-medium text-white mb-2">{c.description}</p>
                                <div className="flex gap-1.5 flex-wrap mb-2">
                                    {c.conflicting_items.map((item, j) => (
                                        <span key={j} className="badge bg-red-500/10 text-red-300 border-red-500/20">
                                            {item}
                                        </span>
                                    ))}
                                </div>
                                {c.suggested_resolution && (
                                    <div className="mt-2 px-3 py-2 bg-emerald-500/5 border border-emerald-500/15 rounded-lg">
                                        <p className="text-xs text-emerald-300">
                                            <span className="font-semibold">Suggested: </span>
                                            {c.suggested_resolution}
                                        </p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default IssuesTab;
