import React from 'react';

export const ScopeDrawer = ({ isOpen, onClose, title, children, side = "right" }) => {
  if (!isOpen) return null;

  const sideClasses = {
    right: "inset-y-0 right-0 h-full w-3/4 border-l sm:max-w-sm",
    left: "inset-y-0 left-0 h-full w-3/4 border-r sm:max-w-sm",
    top: "inset-x-0 top-0 h-auto border-b",
    bottom: "inset-x-0 bottom-0 h-auto border-t"
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />
      
      {/* Drawer Panel */}
      <div className={`fixed z-50 gap-4 bg-white p-6 shadow-lg transition ease-in-out duration-300 ${sideClasses[side]}`}>
        <div className="flex flex-col space-y-1.5 text-left">
          <h2 className="text-lg font-semibold leading-none tracking-tight">{title}</h2>
        </div>
        <div className="py-4 h-full overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
};
