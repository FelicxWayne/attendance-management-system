import apiClient from './client';

export const DEPARTMENTS = [
  { id: 1, name: 'Engineering' },
  { id: 2, name: 'Human Resources' },
  { id: 3, name: 'Finance' },
];

/**
 * Fetches paginated, filtered, and searched employee records.
 * @param {Object} params
 * @param {number} [params.page=1]
 * @param {number} [params.pageSize=10]
 * @param {string} [params.search='']
 * @param {string} [params.status='']
 * @param {number|string} [params.departmentId='']
 * @param {string} [params.sortBy='created_at']
 * @param {string} [params.sortOrder='desc']
 * @returns {Promise<{ items: Array, total: number, page: number, page_size: number, total_pages: number }>}
 */
export async function getEmployeesApi({
  page = 1,
  pageSize = 10,
  search = '',
  status = '',
  departmentId = '',
  sortBy = 'created_at',
  sortOrder = 'desc',
} = {}) {
  const queryParams = {
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_order: sortOrder,
  };

  if (search && search.trim()) {
    queryParams.search = search.trim();
  }

  if (status && (status === 'ACTIVE' || status === 'INACTIVE')) {
    queryParams.status = status;
  }

  if (departmentId && Number(departmentId) > 0) {
    queryParams.department_id = Number(departmentId);
  }

  const response = await apiClient.get('/employees', { params: queryParams });
  return response.data;
}

/**
 * Retrieves full details for an employee by internal database PK.
 * @param {number} id
 * @returns {Promise<Object>}
 */
export async function getEmployeeByIdApi(id) {
  const response = await apiClient.get(`/employees/${id}`);
  return response.data;
}

/**
 * Creates a new employee entity with default ACTIVE status.
 * @param {Object} data
 * @param {string} data.employee_id
 * @param {string} data.name
 * @param {string} data.email
 * @param {string} [data.mobile]
 * @param {number} data.department_id
 * @param {string} data.designation
 * @returns {Promise<Object>}
 */
export async function createEmployeeApi(data) {
  const payload = {
    employee_id: data.employee_id.trim(),
    name: data.name.trim(),
    email: data.email.trim(),
    mobile: data.mobile && data.mobile.trim() ? data.mobile.trim() : null,
    department_id: Number(data.department_id),
    designation: data.designation.trim(),
  };

  const response = await apiClient.post('/employees', payload);
  return response.data;
}

/**
 * Updates an existing employee by internal database PK.
 * @param {number} id
 * @param {Object} data
 * @param {string} data.employee_id
 * @param {string} data.name
 * @param {string} data.email
 * @param {string} [data.mobile]
 * @param {number} data.department_id
 * @param {string} data.designation
 * @param {string} data.status
 * @returns {Promise<Object>}
 */
export async function updateEmployeeApi(id, data) {
  const payload = {
    employee_id: data.employee_id.trim(),
    name: data.name.trim(),
    email: data.email.trim(),
    mobile: data.mobile && data.mobile.trim() ? data.mobile.trim() : null,
    department_id: Number(data.department_id),
    designation: data.designation.trim(),
    status: data.status,
  };

  const response = await apiClient.put(`/employees/${id}`, payload);
  return response.data;
}

/**
 * Logically deactivates an employee by setting status to INACTIVE.
 * Preserves database records and attendance history.
 * @param {number} id
 * @returns {Promise<Object>}
 */
export async function deactivateEmployeeApi(id) {
  const response = await apiClient.delete(`/employees/${id}`);
  return response.data;
}
