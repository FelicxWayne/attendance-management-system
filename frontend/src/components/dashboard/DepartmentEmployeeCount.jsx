import React from 'react';
import { Building2, Users } from 'lucide-react';

export default function DepartmentEmployeeCount({
  departmentCounts = [],
  totalEmployees = 0,
  isLoading = false,
}) {
  return (
    <div className="bg-white p-5 sm:p-6 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div>
          <h2 className="text-base font-bold text-slate-900">Employees by Department</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Headcount distribution across registered departments
          </p>
        </div>
        <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
          <Building2 className="w-4 h-4" />
        </div>
      </div>

      {/* Main List */}
      <div className="py-4 flex-1">
        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            {[1, 2, 3].map((n) => (
              <div key={n} className="space-y-2">
                <div className="flex justify-between items-center">
                  <div className="h-4 bg-slate-200 rounded w-28"></div>
                  <div className="h-4 bg-slate-200 rounded w-10"></div>
                </div>
                <div className="h-2 bg-slate-100 rounded-full w-full"></div>
              </div>
            ))}
          </div>
        ) : departmentCounts.length === 0 ? (
          <div className="py-8 text-center text-slate-400">
            <Building2 className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <p className="text-sm font-medium text-slate-600">No departments found</p>
            <p className="text-xs text-slate-400 mt-0.5">
              Department distribution will appear here once departments are created.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {departmentCounts.map((dept) => {
              const count = dept.employee_count ?? 0;
              const percentage =
                totalEmployees > 0 ? Math.round((count / totalEmployees) * 100) : 0;

              return (
                <div key={dept.department_id} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs sm:text-sm">
                    <span className="font-semibold text-slate-800 truncate pr-2">
                      {dept.department_name}
                    </span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs text-slate-400">
                        {percentage}%
                      </span>
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 min-w-[28px] justify-center">
                        {count}
                      </span>
                    </div>
                  </div>

                  {/* Relative bar */}
                  <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${Math.min(100, Math.max(percentage, count > 0 ? 3 : 0))}%` }}
                      className={`h-full rounded-full transition-all duration-500 ease-out ${
                        count > 0 ? 'bg-indigo-500' : 'bg-transparent'
                      }`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-slate-100 text-xs text-slate-400 flex items-center justify-between">
        <span>Total: {totalEmployees} employee{totalEmployees === 1 ? '' : 's'} (Active + Inactive)</span>
        <span className="font-mono text-2xs">{departmentCounts.length} departments</span>
      </div>
    </div>
  );
}
