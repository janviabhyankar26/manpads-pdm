import axios from "axios";

const BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const api  = axios.create({ baseURL: BASE });

export const getHealthCheck     = ()           => api.get("/health");
export const getUnits           = ()           => api.get("/units");
export const getSummary         = ()           => api.get("/summary");
export const getUnitPredictions = (unitId)     => api.get(`/unit/${unitId}/predict-all`);
export const postPredict        = (sensorData) => api.post("/predict", sensorData);
