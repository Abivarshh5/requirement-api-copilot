import React from 'react';
import type { TabId } from '../types';

interface Tab {
    id: TabId;
    label: string;
    icon: string;
    count?: number;
}

interface TabNavProps {
    activeTab: TabId;
    onTabChange: (tab: TabId) => void;
    counts: Record<TabId, number>;
}

const TABS: Tab[] = [
    { id: 'modules', label: 'Modules', icon: '📦' },
    { id: 'stories', label: 'User Stories', icon: '📖' },
    { id: 'endpoints', label: 'API Endpoints', icon: '🔌' },
    { id: 'database', label: 'Database', icon: '🗄️' },
    { id: 'issues', label: 'Issues', icon: '❓' },
];

const TabNav: React.FC<TabNavProps> = ({ activeTab, onTabChange, counts }) => {
    return (
        <div className="flex gap-1 p-1 bg-surface-800/50 rounded-xl border border-surface-200/10 overflow-x-auto">
            {TABS.map((tab) => {
                const isActive = activeTab === tab.id;
                const count = counts[tab.id] || 0;
                return (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200 ${isActive
                                ? 'bg-brand-600/30 text-brand-200 border border-brand-500/30 shadow-sm'
                                : 'text-surface-200/60 hover:text-surface-200 hover:bg-surface-700/50'
                            }`}
                    >
                        <span>{tab.icon}</span>
                        <span>{tab.label}</span>
                        {count > 0 && (
                            <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${isActive
                                    ? 'bg-brand-500/30 text-brand-200'
                                    : 'bg-surface-700 text-surface-200/50'
                                }`}>
                                {count}
                            </span>
                        )}
                    </button>
                );
            })}
        </div>
    );
};

export default TabNav;
