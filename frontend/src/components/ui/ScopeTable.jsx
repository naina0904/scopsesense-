import React from 'react';

export const ScopeTable = React.forwardRef(({ className = '', children, ...props }, ref) => (
  <div className="relative w-full overflow-auto rounded-2xl border border-slate-100 bg-white">
    <table ref={ref} className={`w-full caption-bottom text-sm ${className}`} {...props}>
      {children}
    </table>
  </div>
));
ScopeTable.displayName = 'ScopeTable';

export const ScopeTableHeader = React.forwardRef(({ className = '', ...props }, ref) => (
  <thead ref={ref} className={`[&_tr]:border-b bg-slate-50/50 ${className}`} {...props} />
));
ScopeTableHeader.displayName = 'ScopeTableHeader';

export const ScopeTableBody = React.forwardRef(({ className = '', ...props }, ref) => (
  <tbody ref={ref} className={`[&_tr:last-child]:border-0 ${className}`} {...props} />
));
ScopeTableBody.displayName = 'ScopeTableBody';

export const ScopeTableRow = React.forwardRef(({ className = '', ...props }, ref) => (
  <tr ref={ref} className={`border-b border-slate-100 transition-colors hover:bg-slate-50/50 data-[state=selected]:bg-slate-50 ${className}`} {...props} />
));
ScopeTableRow.displayName = 'ScopeTableRow';

export const ScopeTableHead = React.forwardRef(({ className = '', ...props }, ref) => (
  <th ref={ref} className={`h-12 px-4 text-left align-middle font-medium text-slate-500 [&:has([role=checkbox])]:pr-0 ${className}`} {...props} />
));
ScopeTableHead.displayName = 'ScopeTableHead';

export const ScopeTableCell = React.forwardRef(({ className = '', ...props }, ref) => (
  <td ref={ref} className={`p-4 align-middle [&:has([role=checkbox])]:pr-0 ${className}`} {...props} />
));
ScopeTableCell.displayName = 'ScopeTableCell';
