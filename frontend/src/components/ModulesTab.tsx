import React, { useState } from 'react';
import type { Module, Feature } from '../types';

interface ModulesTabProps {
    modules: Module[];
    featuresByModule: Record<string, Feature[]>;
}

const priorityBadge = (p: string) => {
    const cls = p === 'high' ? 'badge-high' : p === 'medium' ? 'badge-medium' : 'badge-low';
    return <span className={`badge ${cls}`}>{p}</span>;
};

const complexityLabel = (c: string) => {
    const colors: Record<string, string> = {
        simple: 'text-emerald-400',
        moderate: 'text-amber-400',
        complex: 'text-red-400',
    };
    return <span className={`text-xs font-medium ${colors[c] || 'text-surface-200/50'}`}>{c}</span>;
};

const ModulesTab: React.FC<ModulesTabProps> = ({ modules, featuresByModule }) => {
    const [expanded, setExpanded] = useState<Set<string>>(new Set(modules.map(m => m.module_id)));

    const toggle = (id: string) => {
        setExpanded(prev => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });
    };

    if (modules.length === 0) {
        return (
            <div className="text-center py-10 text-surface-200/40">
                <p className="text-4xl mb-3">📦</p>
                <p>No modules found in this specification.</p>
            </div>
        );
    }

    return (
        <div className="space-y-3 animate-fade-in">
            {modules.map((mod) => {
                const features = featuresByModule[mod.module_id] || [];
                const isOpen = expanded.has(mod.module_id);
                return (
                    <div key={mod.module_id} className="glass-sm overflow-hidden transition-all duration-200">
                        <button
                            onClick={() => toggle(mod.module_id)}
                            className="w-full flex items-center justify-between px-5 py-4 hover:bg-surface-700/30 transition-colors"
                        >
                            <div className="flex items-center gap-3">
                                <span className={`transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}>▶</span>
                                <div className="text-left">
                                    <div className="flex items-center gap-2">
                                        <h3 className="font-semibold text-white">{mod.name}</h3>
                                        {priorityBadge(mod.priority)}
                                    </div>
                                    <p className="text-xs text-surface-200/50 mt-0.5">{mod.description}</p>
                                </div>
                            </div>
                            <span className="text-xs text-surface-200/40 font-mono">
                                {features.length} feature{features.length !== 1 ? 's' : ''}
                            </span>
                        </button>
                        {isOpen && features.length > 0 && (
                            <div className="border-t border-surface-200/5 px-5 py-3 space-y-2">
                                {features.map((feat) => (
                                    <div key={feat.feature_id} className="flex items-start justify-between py-2 px-3 rounded-lg hover:bg-surface-800/30 transition-colors">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-sm font-medium text-surface-50">{feat.name}</span>
                                                {priorityBadge(feat.priority)}
                                                {complexityLabel(feat.complexity)}
                                            </div>
                                            <p className="text-xs text-surface-200/40 mt-0.5">{feat.description}</p>
                                        </div>
                                        <span className="text-[10px] text-surface-200/30 font-mono flex-shrink-0 ml-3">{feat.feature_id}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
};

export default ModulesTab;
