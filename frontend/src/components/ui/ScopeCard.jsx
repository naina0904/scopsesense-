import React from 'react';

export const ScopeCard = React.forwardRef(({ children, className = '', variant = 'soft', ...props }, ref) => {
  const baseStyle = "bg-white border text-slate-900";
  
  // Maps to Lovable's @utility soft-card and lift-card
  const variants = {
    soft: "border-slate-100 rounded-[1.25rem] shadow-sm",
    lift: "border-slate-100 rounded-[1.5rem] shadow-md hover:shadow-lg transition-shadow",
  };

  return (
    <div ref={ref} className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>
      {children}
    </div>
  );
});

ScopeCard.displayName = 'ScopeCard';

export const ScopeCardHeader = ({ children, className = '' }) => (
  <div className={`flex flex-col space-y-1.5 p-6 ${className}`}>
    {children}
  </div>
);

export const ScopeCardTitle = ({ children, className = '' }) => (
  <h3 className={`font-semibold leading-none tracking-tight ${className}`}>
    {children}
  </h3>
);

export const ScopeCardContent = ({ children, className = '' }) => (
  <div className={`p-6 pt-0 ${className}`}>
    {children}
  </div>
);
