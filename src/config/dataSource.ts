// Single switch for the whole app's data source. `true` runs entirely on
// in-memory mock data (src/data/mockData.ts + src/api/mockService.ts) with
// no network calls. `false` calls the real FastAPI backend (src/api/client.ts)
// at EXPO_PUBLIC_API_URL - every src/api/*.ts file branches on this flag.
export const USE_MOCK_DATA = false;
