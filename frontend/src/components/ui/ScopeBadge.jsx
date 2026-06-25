import React from 'react';

export const ScopeBadge = React.forwardRef(({ className = '', variant = 'default', children, ...props }, ref) => {
  const baseStyle = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400";
  
  const variants = {
    default: "border-transparent bg-slate-850 text-white hover:bg-slate-800",
    secondary: "border-transparent bg-slate-100 text-slate-900 hover:bg-slate-200",
    destructive: "border-transparent bg-red-100 text-red-900 hover:bg-red-200",
    outline: "text-slate-900 border-slate-200",
    success: "border-transparent bg-[#9BC5A2] text-slate-900",
    warning: "border-transparent bg-[#EBCFA7] text-slate-900",
  };

  return (
    <div ref={ref} className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>
      {children}
    </div>
  );
});

ScopeBadge.displayName = 'ScopeBadge';
