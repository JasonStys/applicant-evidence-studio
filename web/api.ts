// Purpose: authenticated same-origin API and private downloads; secrets stay in tab memory/session storage.
// Index: fragment@3, initialToken@4, token@9, authorize@18, value@18, api@24, body@24, method@24, path@24, response@25, data@31, download@37, filename@37, path@37, response@38, url@43, link@44, encode@52, file@52, bytes@55, value@56, start@57
const fragment = new URLSearchParams(location.hash.slice(1));
const initialToken = fragment.get('token');
if (initialToken) {
  sessionStorage.setItem('aes-token', initialToken);
  history.replaceState(null, '', location.pathname);
}
let token = sessionStorage.getItem('aes-token') || '';

// A restarted launcher can supply a new token to an existing tab via its URL fragment.
// Reload the module/record state instead of continuing with the previous process session.
window.addEventListener('hashchange', () => {
  if (new URLSearchParams(location.hash.slice(1)).has('token')) location.reload();
});

/** Replace only the session token; applicant data is never placed in browser storage. */
export function authorize(value: string) {
  token = value;
  sessionStorage.setItem('aes-token', value);
}

/** Make a same-origin request and surface controlled error messages without leaking private input. */
export async function api<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/api/' + path, {
    method,
    headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: 'no-store',
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Request failed. Reload and try again.');
  return data as T;
}

/** Download an authenticated private result and revoke its temporary object URL. */
export async function download(path: string, filename: string) {
  const response = await fetch('/api/' + path, {
    headers: { Authorization: 'Bearer ' + token },
    cache: 'no-store',
  });
  if (!response.ok) throw new Error('Download failed; verify your session and selected record.');
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Encode a bounded input without spreading large buffers onto the JavaScript stack. */
export async function encode(file: File): Promise<string> {
  if (file.size > 2_000_000 || file.size === 0)
    throw new Error('Choose a nonempty file no larger than 2 MB.');
  const bytes = new Uint8Array(await file.arrayBuffer());
  let value = '';
  for (let start = 0; start < bytes.length; start += 8192)
    value += String.fromCharCode(...bytes.subarray(start, start + 8192));
  return btoa(value);
}
