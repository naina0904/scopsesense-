import React from 'react';

export const ScopeModal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />
      
      {/* Dialog */}
      <div className="z-50 grid w-full max-w-lg gap-4 bg-white p-6 shadow-lg rounded-[1.5rem] sm:rounded-[2rem] border border-slate-100">
        <div className="flex flex-col space-y-1.5 text-center sm:text-left">
          <h2 className="text-lg font-semibold leading-none tracking-tight">{title}</h2>
        </div>
        <div className="py-4">
          {children}
        </div>
      </div>
    </div>
  );
};
