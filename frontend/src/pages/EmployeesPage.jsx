import React from 'react';
import { Users } from 'lucide-react';
import EmptyState from '../components/EmptyState';

export default function EmployeesPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Employees</h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage employee directory, profiles, departments, and active statuses.
        </p>
      </div>

      {/* Scaffolding Placeholder Card */}
      <EmptyState
        icon={Users}
        title="Employee Directory Under Development"
        description="Employee listings, search, pagination, and record management will be integrated in the upcoming phase."
      />
    </div>
  );
}
