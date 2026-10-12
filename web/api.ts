// Purpose: authenticated same-origin API and private downloads; secrets stay in tab memory/session storage.
// Index: isPrivateWorkspace@3, privateAPI@3, saveFile@4, fragment@5, initialToken@6, token@11, privateService@12, enablePrivateMode@15, authorize@28, value@28, api@34, body@34, method@34, path@34, response@36, data@42, download@48, filename@48, path@48, value@50, response@58, url@63, link@64, encode@72, file@72, bytes@75, value@76, start@77
import { isPrivateWorkspace, privateAPI } from './private-domain';
import { saveFile } from './vault';
const fragment = new URLSearchParams(location.hash.slice(1));
const initialToken = fragment.get('token');
if (initialToken) {
  sessionStorage.setItem('aes-token', initialToken);
  history.replaceState(null, '', location.pathname);
}
let token = sessionStorage.getItem('aes-token') || '';
let privateService = false;

/** Never downgrade to plaintext developer requests after the private service has been detected. */
export function enablePrivateMode() {
  privateService = true;
  token = '';
  sessionStorage.removeItem('aes-token');
}

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
  if (privateService || isPrivateWorkspace()) return privateAPI<T>(path, method, body);
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
  if (privateService || isPrivateWorkspace()) {
    const value = await privateAPI<unknown>(path);
    saveFile(
      typeof value === 'string' ? value : JSON.stringify(value, null, 2),
      filename,
      typeof value === 'string' ? 'text/html' : 'application/json',
    );
    return;
  }
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
