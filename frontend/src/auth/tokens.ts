// Gestão dos tokens JWT no localStorage, num só sítio.
//
// access  → curto (5 min); vai no cabeçalho Authorization: Bearer <access>.
// refresh → mais longo (1 dia); serve para obter um novo access sem novo login.
//
// (localStorage é vulnerável a XSS — para dados sensíveis no futuro, considerar
// cookies httpOnly. Foi uma decisão consciente para esta fase.)

const ACCESS_KEY = "gr_access";
const REFRESH_KEY = "gr_refresh";

export function getAccess(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefresh(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function setAccess(access: string): void {
  localStorage.setItem(ACCESS_KEY, access);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}
