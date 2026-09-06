import apiClient from './client';

/**
 * Fetches consolidated operational dashboard metrics from the FastAPI backend.
 * 
 * Sourced metrics include:
 * - total_employees (active + inactive)
 * - active_employees (status = ACTIVE)
 * - present_today (active employees with attendance on target_date)
 * - absent_today (active employees without attendance on target_date)
 * - department_counts (all departments, including those with 0 employees)
 * 
 * @param {string} [date] - Optional target date in YYYY-MM-DD format (defaults to today in Asia/Kolkata)
 * @returns {Promise<{
 *   total_employees: number,
 *   active_employees: number,
 *   present_today: number,
 *   absent_today: number,
 *   department_counts: Array<{
 *     department_id: number,
 *     department_name: string,
 *     employee_count: number
 *   }>
 * }>}
 */
export async function getDashboardApi(date) {
  const params = {};
  if (date && date.trim()) {
    params.date = date.trim();
  }

  const response = await apiClient.get('/dashboard', { params });
  return response.data;
}
