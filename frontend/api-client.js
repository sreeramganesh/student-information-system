// ============================================================
// API client for the Flask backend
// Replaces supabase-client.js. Function names (sisSignUp,
// sisSignIn, sisRequireRole, etc.) are kept the same so the
// dashboard pages need minimal changes — only the data-fetching
// calls inside each page change from sb.from(...) to api(...).
// ============================================================

const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '5000'
  ? 'http://127.0.0.1:5000/api'
  : `${window.location.origin}/api`;

// ---------- Token storage ----------
function saveToken(token) { localStorage.setItem('sis_token', token); }
function getToken() { return localStorage.getItem('sis_token'); }
function clearToken() { localStorage.removeItem('sis_token'); }

// ---------- Generic authenticated fetch helper ----------
// Usage: await api('/students/me')                       -> GET
//        await api('/students/me', { method: 'PUT', body: {...} })
// Throws an Error with the backend's message on any non-2xx response,
// so callers can use a single try/catch around it.
async function api(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(API_BASE + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (netErr) {
    throw new Error(`Cannot connect to backend (${API_BASE}). Make sure Flask is running on port 5000.`);
  }

  let data = null;
  try { data = await res.json(); } catch (_) { /* empty body is fine */ }

  if (!res.ok) {
    throw new Error((data && data.error) || `Request failed (${res.status})`);
  }
  return data;
}

// ---------- Sign up ----------
// role: 'student' | 'faculty' | 'admin' | 'alumni'
async function sisSignUp({ email, password, fullName, username, role }) {
  try {
    const data = await api('/auth/signup', {
      method: 'POST',
      body: { full_name: fullName, email, username, password, role },
    });
    saveToken(data.token);
    return { data, error: null };
  } catch (err) {
    return { data: null, error: err };
  }
}

// ---------- Sign in ----------
async function sisSignIn({ email, password }) {
  try {
    // The login form sends whatever the person typed as "username" —
    // it might be a username or an email, the backend accepts either.
    const data = await api('/auth/login', {
      method: 'POST',
      body: { username: email, password },
    });
    saveToken(data.token);
    return { data, error: null };
  } catch (err) {
    return { data: null, error: err };
  }
}

// ---------- Sign out ----------
async function sisSignOut() {
  clearToken();
  window.location.href = 'login.html';
}

// ---------- Get current profile ----------
async function sisGetProfile() {
  if (!getToken()) return null;
  try {
    return await api('/auth/me');
  } catch (err) {
    clearToken();
    return null;
  }
}

// ---------- Route guard ----------
async function sisRequireRole(expectedRole) {
  const profile = await sisGetProfile();
  if (!profile) {
    window.location.href = 'login.html';
    return null;
  }
  if (profile.role !== expectedRole) {
    window.location.href = profile.role + '.html';
    return null;
  }
  return profile;
}

// ---------- Small DOM helper ----------
function sisFillText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}
