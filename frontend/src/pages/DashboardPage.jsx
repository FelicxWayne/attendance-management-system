import React from 'react';
import { LayoutDashboard } from 'lucide-react';
import EmptyState from '../components/EmptyState';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Operational metrics, headcount overview, and daily workforce summaries.
        </p>
      </div>

      {/* Scaffolding Placeholder Card */}
      <EmptyState
        icon={LayoutDashboard}
        title="Dashboard Under Development"
        description="Core metrics including total employees, presence counts, and department breakdown will be integrated in the next milestone."
      />
    </div>
  );
}
