import React from 'react';
import { Eye, Edit2, UserX, Mail, Phone, Building2, Briefcase } from 'lucide-react';

export default function EmployeeTable({
  employees,
  onView,
  onEdit,
  onDeactivate,
}) {
  if (!employees || employees.length === 0) {
    return null;
  }

  const renderStatusBadge = (status) => {
    const isActive = status === 'ACTIVE';
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
          isActive
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
            : 'bg-slate-100 text-slate-600 border-slate-200'
        }`}
      >
        <span
          className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
            isActive ? 'bg-emerald-500' : 'bg-slate-400'
          }`}
        />
        {status}
      </span>
    );
  };

  return (
    <div className="w-full">
      {/* Desktop & Tablet Table (>= 768px) */}
      <div className="hidden md:block overflow-x-auto bg-white rounded-xl border border-slate-200 shadow-xs">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm" aria-label="Employees Table">
          <thead className="bg-slate-50 text-slate-500 font-medium">
            <tr>
              <th scope="col" className="px-4 py-3.5 whitespace-nowrap">Employee ID</th>
              <th scope="col" className="px-4 py-3.5 whitespace-nowrap">Name</th>
              <th scope="col" className="px-4 py-3.5 whitespace-nowrap">Email</th>
              <th scope="col" className="px-4 py-3.5 whitespace-nowrap">Mobile</th>
              <th scope="col" className="px-4 py-3.5 whitespace-nowrap">Department</th>
              <th scope="col" className="px-4 py-3.5 whitespace-nowrap">Designation</th>
              <th scope="col" className="px-4 py-3.5 whitespace-nowrap">Status</th>
              <th scope="col" className="px-4 py-3.5 text-right whitespace-nowrap">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {employees.map((emp) => (
              <tr key={emp.id} className="hover:bg-slate-50/70 transition-colors">
                <td className="px-4 py-3.5 font-semibold text-slate-900 whitespace-nowrap">
                  {emp.employee_id}
                </td>
                <td className="px-4 py-3.5 font-medium text-slate-800 whitespace-nowrap">
                  {emp.name}
                </td>
                <td className="px-4 py-3.5 text-slate-600 whitespace-nowrap">
                  {emp.email}
                </td>
                <td className="px-4 py-3.5 text-slate-600 whitespace-nowrap">
                  {emp.mobile || '—'}
                </td>
                <td className="px-4 py-3.5 text-slate-700 whitespace-nowrap">
                  {emp.department_name || emp.department?.name || '—'}
                </td>
                <td className="px-4 py-3.5 text-slate-600 whitespace-nowrap">
                  {emp.designation}
                </td>
                <td className="px-4 py-3.5 whitespace-nowrap">
                  {renderStatusBadge(emp.status)}
                </td>
                <td className="px-4 py-3.5 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      type="button"
                      onClick={() => onView(emp)}
                      className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="View employee details"
                      aria-label={`View ${emp.name}`}
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => onEdit(emp)}
                      className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
                      title="Edit employee"
                      aria-label={`Edit ${emp.name}`}
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => onDeactivate(emp)}
                      disabled={emp.status === 'INACTIVE'}
                      className={`p-1.5 rounded-lg transition-colors ${
                        emp.status === 'INACTIVE'
                          ? 'text-slate-300 cursor-not-allowed'
                          : 'text-slate-500 hover:text-red-600 hover:bg-red-50'
                      }`}
                      title={emp.status === 'INACTIVE' ? 'Already Inactive' : 'Deactivate employee'}
                      aria-label={`Deactivate ${emp.name}`}
                    >
                      <UserX className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Responsive Cards (< 768px) */}
      <div className="grid grid-cols-1 gap-3 md:hidden">
        {employees.map((emp) => (
          <div
            key={emp.id}
            className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col space-y-3"
          >
            {/* Card Header: Name, Employee ID & Status */}
            <div className="flex items-start justify-between gap-2 border-b border-slate-100 pb-2.5">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900 text-sm">{emp.name}</span>
                </div>
                <span className="text-xs font-mono font-medium text-slate-500">{emp.employee_id}</span>
              </div>
              <div>{renderStatusBadge(emp.status)}</div>
            </div>

            {/* Card Body Details */}
            <div className="grid grid-cols-1 gap-1.5 text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <Briefcase className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="font-medium text-slate-700">{emp.designation}</span>
              </div>
              <div className="flex items-center gap-2">
                <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span>{emp.department_name || emp.department?.name || '—'}</span>
              </div>
              <div className="flex items-center gap-2 truncate">
                <Mail className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="truncate">{emp.email}</span>
              </div>
              {emp.mobile && (
                <div className="flex items-center gap-2">
                  <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span>{emp.mobile}</span>
                </div>
              )}
            </div>

            {/* Card Action Buttons */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => onView(emp)}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>View</span>
              </button>
              <button
                type="button"
                onClick={() => onEdit(emp)}
                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-md transition-colors"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>Edit</span>
              </button>
              <button
                type="button"
                onClick={() => onDeactivate(emp)}
                disabled={emp.status === 'INACTIVE'}
                className={`inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  emp.status === 'INACTIVE'
                    ? 'text-slate-400 bg-slate-100 cursor-not-allowed'
                    : 'text-red-700 bg-red-50 hover:bg-red-100'
                }`}
              >
                <UserX className="w-3.5 h-3.5" />
                <span>Deactivate</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
