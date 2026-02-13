import React, { useState } from 'react';

interface RefineModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (instructions: string) => void;
    isLoading: boolean;
}

const RefineModal: React.FC<RefineModalProps> = ({ isOpen, onClose, onSubmit, isLoading }) => {
    const [instructions, setInstructions] = useState('');

    if (!isOpen) return null;

    const handleSubmit = () => {
        if (instructions.trim().length < 5) return;
        onSubmit(instructions.trim());
    };

    const handleBackdrop = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget && !isLoading) {
            onClose();
        }
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
            onClick={handleBackdrop}
        >
            <div className="glass w-full max-w-lg mx-4 p-6 animate-slide-up">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <span>🔄</span> Refine Specification
                    </h3>
                    {!isLoading && (
                        <button onClick={onClose} className="text-surface-200/40 hover:text-surface-200 transition-colors text-lg">
                            ✕
                        </button>
                    )}
                </div>

                <p className="text-sm text-surface-200/60 mb-4">
                    Describe what changes you'd like to make. The AI will update the specification while preserving existing elements.
                </p>

                <textarea
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    placeholder="E.g., Add OAuth2 authentication to all endpoints, Add a notifications module, Include pagination for all list endpoints..."
                    className="w-full h-32 px-4 py-3 bg-surface-800/50 border border-surface-200/10 rounded-xl text-surface-50 placeholder-surface-200/30 resize-y focus:outline-none focus:ring-2 focus:ring-brand-500/50 text-sm leading-relaxed"
                    disabled={isLoading}
                />

                <div className="flex justify-end gap-3 mt-4">
                    <button
                        onClick={onClose}
                        disabled={isLoading}
                        className="btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading || instructions.trim().length < 5}
                        className="btn-primary flex items-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                </svg>
                                Refining...
                            </>
                        ) : (
                            <>Apply Refinement</>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default RefineModal;
