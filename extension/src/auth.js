const SUPABASE_URL = "https://zlqdjqnfagayywuzaspn.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscWRqcW5mYWdheXl3dXphc3BuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ4ODY4NjUsImV4cCI6MjA5MDQ2Mjg2NX0.hJeet20l8Ri7IGoXnqyyJFIn85VfpCCcf2RFBHCjpDw";

const STORAGE_KEY = "auth";

// ── Helpers ───────────────────────────────────────────────────────────────────

function getRedirectUrl() {
  return chrome.identity.getRedirectURL("callback");
}

function parseHashParams(url) {
  const hash = new URL(url).hash.slice(1);
  return Object.fromEntries(new URLSearchParams(hash));
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function getSession() {
  const { auth } = await chrome.storage.local.get([STORAGE_KEY]);
  return auth || null;
}

export async function getAccessToken() {
  let session = await getSession();
  if (!session) return null;

  // Refresh if token expires within 60 seconds
  const expiresAt = session.expires_at * 1000;
  if (Date.now() >= expiresAt - 60_000) {
    session = await refreshSession(session.refresh_token);
  }

  return session?.access_token || null;
}

export async function login() {
  const redirectUrl = getRedirectUrl();

  const authUrl =
    `${SUPABASE_URL}/auth/v1/authorize` +
    `?provider=google` +
    `&redirect_to=${encodeURIComponent(redirectUrl)}`;

  const responseUrl = await chrome.identity.launchWebAuthFlow({
    url: authUrl,
    interactive: true,
  });

  const params = parseHashParams(responseUrl);
  if (!params.access_token) throw new Error("Login failed: no token returned");

  const session = {
    access_token: params.access_token,
    refresh_token: params.refresh_token,
    expires_at: Math.floor(Date.now() / 1000) + parseInt(params.expires_in || "3600"),
  };

  await chrome.storage.local.set({ [STORAGE_KEY]: session });
  return session;
}

export async function logout() {
  await chrome.storage.local.remove(STORAGE_KEY);
}

export async function refreshSession(refreshToken) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "apikey": SUPABASE_ANON_KEY,
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) {
    // Refresh failed — force re-login
    await logout();
    return null;
  }

  const data = await res.json();
  const session = {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: Math.floor(Date.now() / 1000) + data.expires_in,
  };

  await chrome.storage.local.set({ [STORAGE_KEY]: session });
  return session;
}
