import { post, get } from "../utils/request";

export const login = (username, password) => {
  return post("/auth/login", {
    username,
    password,
  });
};

export const refreshToken = (refreshToken) => {
  return post("/auth/refresh", {
    refresh_token: refreshToken,
  });
};

export const getCurrentUser = () => {
  return get("/auth/me");
};
