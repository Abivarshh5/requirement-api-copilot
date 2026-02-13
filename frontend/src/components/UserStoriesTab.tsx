import React, { useState } from 'react';
import type { UserStory, Module } from '../types';

interface UserStoriesTabProps {
    stories: UserStory[];
    modules: Module[];
}

const UserStoriesTab: React.FC<UserStoriesTabProps> = ({ stories, modules }) => {
    const [filterModule, setFilterModule] = useState<string>('all');
    const [filterPriority, setFilterPriority] = useState<string>('all');
    const [search, setSearch] = useState('');

    const filtered = stories.filter((s) => {
        if (filterModule !== 'all' && s.module_id !== filterModule) return false;
        if (filterPriority !== 'all' && s.priority !== filterPriority) return false;
        if (search) {
            const q = search.toLowerCase();
            return (
                s.as_a.toLowerCase().includes(q) ||
                s.i_want.toLowerCase().includes(q) ||
                s.so_that.toLowerCase().includes(q)
            );
        }
        return true;
    });

    if (stories.length === 0) {
        return (
            <div className="text-center py-10 text-surface-200/40">
                <p className="text-4xl mb-3">📖</p>
                <p>No user stories generated yet.</p>
            </div>
        );
    }

    return (
        <div className="animate-fade-in">
            {/* Filters */}
            <div className="flex flex-wrap gap-3 mb-4">
                <input
                    type="text"
                    placeholder="Search stories..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="px-3 py-2 bg-surface-800/50 border border-surface-200/10 rounded-lg text-sm text-surface-50 placeholder-surface-200/30 focus:outline-none focus:ring-2 focus:ring-brand-500/40 w-48"
                />
                <select
                    value={filterModule}
                    onChange={(e) => setFilterModule(e.target.value)}
                    className="px-3 py-2 bg-surface-800/50 border border-surface-200/10 rounded-lg text-sm text-surface-50 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                >
                    <option value="all">All Modules</option>
                    {modules.map((m) => (
                        <option key={m.module_id} value={m.module_id}>{m.name}</option>
                    ))}
                </select>
                <select
                    value={filterPriority}
                    onChange={(e) => setFilterPriority(e.target.value)}
                    className="px-3 py-2 bg-surface-800/50 border border-surface-200/10 rounded-lg text-sm text-surface-50 focus:outline-none focus:ring-2 focus:ring-brand-500/40"
                >
                    <option value="all">All Priorities</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
                <span className="text-xs text-surface-200/40 self-center ml-auto">
                    {filtered.length} of {stories.length} stories
                </span>
            </div>

            {/* Story Cards */}
            <div className="grid gap-3 md:grid-cols-2">
                {filtered.map((story) => {
                    const mod = modules.find(m => m.module_id === story.module_id);
                    return (
                        <div key={story.story_id} className="glass-sm p-4 hover:border-brand-500/20 transition-all duration-200">
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-2 flex-wrap">
                                    {mod && (
                                        <span className="badge bg-brand-500/15 text-brand-300 border border-brand-500/20">
                                            {mod.name}
                                        </span>
                                    )}
                                    <span className={`badge ${story.priority === 'high' ? 'badge-high' : story.priority === 'medium' ? 'badge-medium' : 'badge-low'}`}>
                                        {story.priority}
                                    </span>
                                </div>
                                <span className="text-[10px] text-surface-200/30 font-mono">{story.story_id}</span>
                            </div>

                            <div className="space-y-1.5 mb-3">
                                <p className="text-sm">
                                    <span className="text-surface-200/50">As a </span>
                                    <span className="font-semibold text-white">{story.as_a}</span>
                                </p>
                                <p className="text-sm">
                                    <span className="text-surface-200/50">I want </span>
                                    <span className="text-surface-50">{story.i_want}</span>
                                </p>
                                <p className="text-sm">
                                    <span className="text-surface-200/50">So that </span>
                                    <span className="italic text-surface-200/70">{story.so_that}</span>
                                </p>
                            </div>

                            {story.acceptance_criteria.length > 0 && (
                                <div className="pt-3 border-t border-surface-200/5">
                                    <p className="text-[10px] text-surface-200/40 uppercase font-semibold tracking-wider mb-1.5">Acceptance Criteria</p>
                                    <ul className="space-y-1">
                                        {story.acceptance_criteria.map((ac, i) => (
                                            <li key={i} className="flex items-start gap-2 text-xs text-surface-200/60">
                                                <span className="text-brand-400 mt-0.5">✓</span>
                                                <span>{ac}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default UserStoriesTab;
