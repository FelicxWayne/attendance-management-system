import React from 'react';
import { CalendarCheck } from 'lucide-react';
import EmptyState from '../components/EmptyState';

export default function AttendancePage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Attendance</h1>
        <p className="text-sm text-slate-500 mt-1">
          Daily attendance tracking, check-in, check-out, and attendance logs.
        </p>
      </div>

      {/* Scaffolding Placeholder Card */}
      <EmptyState
        icon={CalendarCheck}
        title="Attendance Tracking Under Development"
        description="Daily status summaries, check-in and check-out logs, and date filtering will be integrated in the upcoming phase."
      />
    </div>
  );
}
