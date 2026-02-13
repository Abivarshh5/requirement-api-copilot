import React from 'react';

interface InputPanelProps {
    value: string;
    onChange: (value: string) => void;
    onGenerate: () => void;
    isLoading: boolean;
    error: string | null;
}

const SAMPLE_REQUIREMENTS = `We need a task management system for small teams. Users should be able to:

1. Sign up and log in with email and password
2. Create projects and invite team members
3. Create tasks within projects with title, description, priority, and due date
4. Assign tasks to team members
5. Update task status (To Do, In Progress, In Review, Done)
6. Add comments on tasks
7. Get notifications when assigned to a task or when someone comments
8. View a dashboard with task statistics and project progress
9. Search and filter tasks by status, priority, assignee, and due date
10. Admin users should be able to manage team members and project settings`;

const InputPanel: React.FC<InputPanelProps> = ({ value, onChange, onGenerate, isLoading, error }) => {
    const charCount = value.length;
    const isValid = charCount >= 50 && charCount <= 10000;
    const handleLoadSample = () => {
        onChange(SAMPLE_REQUIREMENTS);
    };

    return (
        <div className="glass p-6 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center">
                        <span className="text-white text-sm">📝</span>
                    </div>
                    <h2 className="text-lg font-semibold text-white">Input Requirements</h2>
                </div>
                <button
                    onClick={handleLoadSample}
                    className="btn-ghost text-sm flex items-center gap-1.5"
                >
                    <span>✨</span> Load Sample
                </button>
            </div>

            <div className="relative">
                <textarea
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder="Paste your product requirements here...&#10;&#10;Example: We need a user authentication system with email and password login. Users should be able to sign up, log in, reset their password, and manage their profile..."
                    className="w-full h-52 px-4 py-3 bg-surface-800/50 border border-surface-200/10 rounded-xl text-surface-50 placeholder-surface-200/30 resize-y focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition-all font-sans text-sm leading-relaxed"
                    disabled={isLoading}
                    maxLength={10000}
                />
                <div className={`absolute bottom-3 right-3 text-xs font-mono ${charCount === 0 ? 'text-surface-200/30' :
                    charCount < 50 ? 'text-red-400' :
                        charCount > 9500 ? 'text-amber-400' :
                            'text-surface-200/50'
                    }`}>
                    {charCount.toLocaleString()} / 10,000
                </div>
            </div>

            {error && (
                <div className="mt-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-300 text-sm flex items-start gap-2">
                    <span className="mt-0.5">⚠️</span>
                    <span>{error}</span>
                </div>
            )}

            <div className="flex items-center gap-3 mt-4">
                <button
                    onClick={onGenerate}
                    disabled={!isValid || isLoading}
                    className="btn-primary flex items-center gap-2"
                >
                    {isLoading ? (
                        <>
                            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            <span>Generating...</span>
                        </>
                    ) : (
                        <>
                            <span>🚀</span>
                            <span>Generate Specification</span>
                        </>
                    )}
                </button>
                <button
                    onClick={() => onChange('')}
                    disabled={isLoading || charCount === 0}
                    className="btn-secondary"
                >
                    Clear
                </button>
                {charCount > 0 && charCount < 50 && (
                    <span className="text-xs text-red-400/70">
                        Need {50 - charCount} more characters
                    </span>
                )}
            </div>
        </div>
    );
};

export default InputPanel;
