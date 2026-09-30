// Purpose: authenticated same-origin API and private downloads; secrets stay in tab memory/session storage.
// Index: fragment@3, initialToken@4, token@9, authorize@12, value@12, api@18, body@18, method@18, path@18, response@19, data@25, download@31, filename@31, path@31, response@32, url@37, link@38, encode@46, file@46, bytes@49, value@50, start@51
const fragment = new URLSearchParams(location.hash.slice(1));
const initialToken = fragment.get('token');
if (initialToken) {
  sessionStorage.setItem('aes-token', initialToken);
  history.replaceState(null, '', location.pathname);
}
let token = sessionStorage.getItem('aes-token') || '';

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
