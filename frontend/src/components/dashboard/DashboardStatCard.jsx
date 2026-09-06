import React from 'react';

const COLOR_SCHEMES = {
  blue: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    border: 'border-l-blue-500',
    valueText: 'text-slate-900',
  },
  indigo: {
    bg: 'bg-indigo-50',
    text: 'text-indigo-600',
    border: 'border-l-indigo-500',
    valueText: 'text-slate-900',
  },
  emerald: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-600',
    border: 'border-l-emerald-500',
    valueText: 'text-emerald-700',
  },
  rose: {
    bg: 'bg-rose-50',
    text: 'text-rose-600',
    border: 'border-l-rose-500',
    valueText: 'text-rose-700',
  },
};

export default function DashboardStatCard({
  title,
  value,
  icon: Icon,
  colorScheme = 'blue',
  subtitle,
  isLoading = false,
}) {
  const scheme = COLOR_SCHEMES[colorScheme] || COLOR_SCHEMES.blue;

  return (
    <div
      className={`bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center gap-4 transition-all hover:border-slate-300 border-l-4 ${scheme.border}`}
    >
      {/* Icon container */}
      <div
        className={`w-12 h-12 rounded-xl ${scheme.bg} ${scheme.text} flex items-center justify-center shrink-0`}
      >
        {Icon && <Icon className="w-6 h-6" aria-hidden="true" />}
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {title}
        </p>

        {isLoading ? (
          <div className="mt-1 space-y-1.5 animate-pulse">
            <div className="h-7 w-16 bg-slate-200 rounded"></div>
            <div className="h-3.5 w-24 bg-slate-100 rounded"></div>
          </div>
        ) : (
          <div className="mt-1">
            <div className="flex items-baseline gap-2">
              <span className={`text-2xl font-bold tracking-tight ${scheme.valueText}`}>
                {value ?? 0}
              </span>
            </div>
            {subtitle && (
              <p className="text-xs text-slate-400 mt-0.5 truncate">
                {subtitle}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
