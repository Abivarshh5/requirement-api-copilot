import React from 'react';
import type { DbTable } from '../types';

interface DatabaseTabProps {
    tables: DbTable[];
}

const DatabaseTab: React.FC<DatabaseTabProps> = ({ tables }) => {
    if (tables.length === 0) {
        return (
            <div className="text-center py-10 text-surface-200/40">
                <p className="text-4xl mb-3">🗄️</p>
                <p>No database tables generated yet.</p>
            </div>
        );
    }

    return (
        <div className="space-y-4 animate-fade-in">
            {tables.map((table) => (
                <div key={table.table_name} className="glass-sm overflow-hidden">
                    {/* Table Header */}
                    <div className="px-5 py-4 border-b border-surface-200/5">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="text-lg">🗄️</span>
                                <div>
                                    <h3 className="font-mono font-semibold text-white">{table.table_name}</h3>
                                    <p className="text-xs text-surface-200/50 mt-0.5">{table.description}</p>
                                </div>
                            </div>
                            <span className="text-xs text-surface-200/40">
                                {table.columns.length} columns
                            </span>
                        </div>
                    </div>

                    {/* Columns Table */}
                    <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                            <thead>
                                <tr className="bg-surface-800/40">
                                    <th className="text-left px-4 py-2.5 font-semibold text-surface-200/60 uppercase tracking-wider">Column</th>
                                    <th className="text-left px-4 py-2.5 font-semibold text-surface-200/60 uppercase tracking-wider">Type</th>
                                    <th className="text-center px-4 py-2.5 font-semibold text-surface-200/60 uppercase tracking-wider">Null</th>
                                    <th className="text-center px-4 py-2.5 font-semibold text-surface-200/60 uppercase tracking-wider">Key</th>
                                    <th className="text-left px-4 py-2.5 font-semibold text-surface-200/60 uppercase tracking-wider">Default</th>
                                    <th className="text-left px-4 py-2.5 font-semibold text-surface-200/60 uppercase tracking-wider">Constraints</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-200/5">
                                {table.columns.map((col) => (
                                    <tr key={col.name} className="hover:bg-surface-700/20 transition-colors">
                                        <td className="px-4 py-2.5">
                                            <div className="flex items-center gap-2">
                                                <span className="font-mono text-surface-50">{col.name}</span>
                                                {col.primary_key && (
                                                    <span className="text-amber-400" title="Primary Key">🔑</span>
                                                )}
                                                {col.foreign_key && (
                                                    <span className="text-blue-400" title={`FK: ${col.foreign_key}`}>🔗</span>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-4 py-2.5 font-mono text-brand-300">{col.type}</td>
                                        <td className="px-4 py-2.5 text-center">
                                            {col.nullable ? (
                                                <span className="text-surface-200/40">YES</span>
                                            ) : (
                                                <span className="text-red-400 font-semibold">NO</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-2.5 text-center">
                                            {col.primary_key && <span className="badge bg-amber-500/15 text-amber-300 border border-amber-500/20">PK</span>}
                                            {col.foreign_key && <span className="badge bg-blue-500/15 text-blue-300 border border-blue-500/20">FK</span>}
                                        </td>
                                        <td className="px-4 py-2.5 font-mono text-surface-200/50">{col.default != null ? String(col.default) : '—'}</td>
                                        <td className="px-4 py-2.5">
                                            <div className="flex gap-1 flex-wrap">
                                                {col.constraints.map((c, i) => (
                                                    <span key={i} className="badge bg-surface-700 text-surface-200/60 border-surface-200/10">{c}</span>
                                                ))}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Indexes & Relationships */}
                    {(table.indexes.length > 0 || table.relationships.length > 0) && (
                        <div className="px-5 py-3 border-t border-surface-200/5 flex gap-6 flex-wrap">
                            {table.indexes.length > 0 && (
                                <div>
                                    <p className="text-[10px] text-surface-200/40 uppercase font-semibold tracking-wider mb-1">Indexes</p>
                                    <div className="flex gap-1.5 flex-wrap">
                                        {table.indexes.map((idx) => (
                                            <span key={idx.name} className={`badge ${idx.unique ? 'bg-amber-500/15 text-amber-300 border-amber-500/20' : 'bg-surface-700 text-surface-200/60 border-surface-200/10'}`}>
                                                {idx.name} ({idx.columns.join(', ')}) {idx.unique ? '• UNIQUE' : ''}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {table.relationships.length > 0 && (
                                <div>
                                    <p className="text-[10px] text-surface-200/40 uppercase font-semibold tracking-wider mb-1">Relationships</p>
                                    <div className="space-y-1">
                                        {table.relationships.map((rel, i) => (
                                            <p key={i} className="text-xs text-surface-200/60">
                                                <span className="badge bg-purple-500/15 text-purple-300 border-purple-500/20 mr-1">{rel.type}</span>
                                                → <span className="font-mono text-surface-50">{rel.target_table}</span>
                                                <span className="text-surface-200/40 ml-1">({rel.description})</span>
                                            </p>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
};

export default DatabaseTab;
