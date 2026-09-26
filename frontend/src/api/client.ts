/**
 * KameraPh API Client Gateway
 * Re-exports the enterprise Axios apiClient with global interceptors.
 */

import { apiClient } from './apiClient';

export { apiClient, apiClient as api };
export default apiClient;
