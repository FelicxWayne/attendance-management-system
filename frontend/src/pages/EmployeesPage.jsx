import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Users, RefreshCw, CheckCircle2 } from 'lucide-react';
import {
  getEmployeesApi,
  createEmployeeApi,
  updateEmployeeApi,
  deactivateEmployeeApi,
} from '../api/employees';
import EmployeeFilters from '../components/employee/EmployeeFilters';
import EmployeeTable from '../components/employee/EmployeeTable';
import EmployeeFormModal from '../components/employee/EmployeeFormModal';
import EmployeeDetailsModal from '../components/employee/EmployeeDetailsModal';
import ConfirmDeactivateModal from '../components/employee/ConfirmDeactivateModal';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';
import EmptyState from '../components/EmptyState';

export default function EmployeesPage() {
  // Data state
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);

  // Filter & Search state
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [departmentId, setDepartmentId] = useState('');

  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Modal states
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [formInitialData, setFormInitialData] = useState(null);

  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [viewingEmployee, setViewingEmployee] = useState(null);

  const [isDeactivateModalOpen, setIsDeactivateModalOpen] = useState(false);
  const [deactivatingEmployee, setDeactivatingEmployee] = useState(null);

  // Auto-dismiss success message after 5 seconds
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  // Fetch employees from backend
  const fetchEmployees = useCallback(
    async (currentPage = page) => {
      setIsLoading(true);
      setErrorMessage('');

      try {
        const data = await getEmployeesApi({
          page: currentPage,
          pageSize,
          search,
          status,
          departmentId,
        });

        setEmployees(data.items || []);
        setTotal(data.total || 0);
        setPage(data.page || 1);
        setTotalPages(data.total_pages || 1);
      } catch (err) {
        if (err.response?.data?.detail) {
          setErrorMessage(String(err.response.data.detail));
        } else if (err.code === 'ERR_NETWORK' || !err.response) {
          setErrorMessage('Unable to connect to the server. Please check your network connection.');
        } else {
          setErrorMessage('Failed to load employee records. Please try again.');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [page, pageSize, search, status, departmentId]
  );

  // Fetch on mount or when filters change
  useEffect(() => {
    fetchEmployees(page);
  }, [fetchEmployees, page]);

  // Reset to page 1 when search or filters change
  const handleSearchChange = (value) => {
    setSearch(value);
    setPage(1);
  };

  const handleStatusChange = (value) => {
    setStatus(value);
    setPage(1);
  };

  const handleDepartmentChange = (value) => {
    setDepartmentId(value);
    setPage(1);
  };

  const handleResetFilters = () => {
    setSearch('');
    setStatus('');
    setDepartmentId('');
    setPage(1);
  };

  // Open Add Modal
  const handleOpenAddModal = () => {
    setFormInitialData(null);
    setIsFormModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (employee) => {
    setFormInitialData(employee);
    setIsFormModalOpen(true);
  };

  // Open View Details Modal
  const handleOpenViewModal = (employee) => {
    setViewingEmployee(employee);
    setIsDetailsModalOpen(true);
  };

  // Open Deactivate Confirmation Modal
  const handleOpenDeactivateModal = (employee) => {
    setDeactivatingEmployee(employee);
    setIsDeactivateModalOpen(true);
  };

  // Create or Update submit handler
  const handleFormSubmit = async (formData) => {
    if (formInitialData) {
      // Update operation
      await updateEmployeeApi(formInitialData.id, formData);
      setSuccessMessage(`Employee '${formData.name}' was successfully updated.`);
      fetchEmployees(page);
    } else {
      // Create operation
      await createEmployeeApi(formData);
      setSuccessMessage(`Employee '${formData.name}' was successfully created.`);
      // Return to first page to see the new entry
      setPage(1);
      fetchEmployees(1);
    }
  };

  // Deactivate confirm handler
  const handleConfirmDeactivate = async (id) => {
    const updated = await deactivateEmployeeApi(id);
    setSuccessMessage(`Employee '${updated.name}' has been deactivated. Historical records are preserved.`);
    fetchEmployees(page);
  };

  // Pagination calculation
  const startIndex = total > 0 ? (page - 1) * pageSize + 1 : 0;
  const endIndex = Math.min(page * pageSize, total);
  const hasActiveFilters = Boolean(search || status || departmentId);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Employees</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage employee directory, profiles, departments, and active statuses.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => fetchEmployees(page)}
            disabled={isLoading}
            className="p-2 text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
            title="Refresh employees"
            aria-label="Refresh employees"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
          </button>
          <button
            type="button"
            id="add-employee-button"
            onClick={handleOpenAddModal}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <Plus className="w-4 h-4" />
            <span>Add Employee</span>
          </button>
        </div>
      </div>

      {/* Success Notification Alert */}
      {successMessage && (
        <div
          role="status"
          className="flex items-center justify-between p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-sm"
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setSuccessMessage('')}
            className="text-emerald-500 hover:text-emerald-800 text-sm font-medium ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* API Error Alert */}
      {errorMessage && (
        <ErrorAlert
          message={errorMessage}
          onDismiss={() => setErrorMessage('')}
        />
      )}

      {/* Filter and Search Bar */}
      <EmployeeFilters
        search={search}
        status={status}
        departmentId={departmentId}
        onSearchChange={handleSearchChange}
        onStatusChange={handleStatusChange}
        onDepartmentChange={handleDepartmentChange}
        onResetFilters={handleResetFilters}
      />

      {/* Main Content Area */}
      {isLoading ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12">
          <LoadingSpinner message="Loading employee directory..." />
        </div>
      ) : employees.length === 0 ? (
        hasActiveFilters ? (
          <EmptyState
            icon={Users}
            title="No matching employees found"
            description="No employee records matched your active search and filter criteria. Try adjusting or clearing your filters."
            action={
              <button
                type="button"
                onClick={handleResetFilters}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
              >
                Clear Filters
              </button>
            }
          />
        ) : (
          <EmptyState
            icon={Users}
            title="No employees registered yet"
            description="Your organization does not have any employee records in the system. Add your first employee to get started."
            action={
              <button
                type="button"
                onClick={handleOpenAddModal}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-xs"
              >
                <Plus className="w-4 h-4" />
                <span>Add Employee</span>
              </button>
            }
          />
        )
      ) : (
        <div className="space-y-4">
          {/* Table / Cards */}
          <EmployeeTable
            employees={employees}
            onView={handleOpenViewModal}
            onEdit={handleOpenEditModal}
            onDeactivate={handleOpenDeactivateModal}
          />

          {/* Pagination Footer Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white px-4 py-3 rounded-xl border border-slate-200 shadow-xs text-sm text-slate-600">
            <div>
              Showing <span className="font-semibold text-slate-800">{startIndex}</span> to{' '}
              <span className="font-semibold text-slate-800">{endIndex}</span> of{' '}
              <span className="font-semibold text-slate-800">{total}</span> employees
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 mr-2">
                Page {page} of {totalPages || 1}
              </span>
              <button
                type="button"
                onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                disabled={page <= 1 || isLoading}
                className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))}
                disabled={page >= totalPages || isLoading}
                className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Modal */}
      <EmployeeFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        onSubmit={handleFormSubmit}
        initialData={formInitialData}
      />

      {/* View Details Modal */}
      <EmployeeDetailsModal
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        employee={viewingEmployee}
        onEdit={(emp) => {
          setIsDetailsModalOpen(false);
          handleOpenEditModal(emp);
        }}
      />

      {/* Confirm Deactivate Modal */}
      <ConfirmDeactivateModal
        isOpen={isDeactivateModalOpen}
        onClose={() => setIsDeactivateModalOpen(false)}
        onConfirm={handleConfirmDeactivate}
        employee={deactivatingEmployee}
      />
    </div>
  );
}
