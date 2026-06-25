import React from 'react';

export const ScopeButton = React.forwardRef(({ children, className = '', variant = 'primary', ...props }, ref) => {
  // Temporary mapping until Tailwind config is fully updated
  // Primary maps to 'ink', secondary to 'beige'
  const baseStyle = "inline-flex items-center justify-center rounded-2xl text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 disabled:opacity-50 disabled:pointer-events-none ring-offset-background";
  const variants = {
    primary: "bg-slate-850 text-white hover:bg-slate-800",
    secondary: "bg-[#F4EDE4] text-[#1F2937] hover:bg-[#E8CFCB]",
    outline: "border border-slate-200 hover:bg-slate-100",
    ghost: "hover:bg-slate-100 text-slate-800",
  };
  const sizeStyles = "h-10 py-2 px-4";

  return (
    <button
      ref={ref}
      className={`${baseStyle} ${variants[variant]} ${sizeStyles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
});

ScopeButton.displayName = 'ScopeButton';
