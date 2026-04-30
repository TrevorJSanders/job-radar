import axios from "axios";

const api = axios.create({
  baseURL: "/api", // Proxied to http://localhost:8000 in dev
});

export const checkHealth = async () => {
  const { data } = await api.get("/health");
  return data;
};

export default api;
