import React from 'react';

export const ScopeProgress = React.forwardRef(({ className = '', value = 0, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={`relative h-4 w-full overflow-hidden rounded-full bg-slate-100 ${className}`}
      {...props}
    >
      <div
        className="h-full w-full flex-1 bg-slate-850 transition-all duration-500 ease-in-out"
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </div>
  );
});

ScopeProgress.displayName = 'ScopeProgress';
