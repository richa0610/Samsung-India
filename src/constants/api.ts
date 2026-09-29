// The backend URL is runtime-configurable (gear icon on the role screen) so
// a changed PC IP / Wi-Fi never needs a rebuild - see src/config/serverUrl.ts.
// Import the getters, not a constant: they resolve per call so an edit takes
// effect on the next request without an app restart.
export { getApiBaseUrl, getWsBaseUrl, DEFAULT_API_URL } from "@/config/serverUrl";
