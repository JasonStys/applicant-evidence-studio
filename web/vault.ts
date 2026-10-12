// Purpose: Jason Stys — browser-only encryption, ciphertext sync and versioned encrypted backups.
// Index: Envelope@3, VAULT_LIMIT@9, encoder@10, decoder@11, context@12, base64@15, bytes@15, text@16, i@17, validateEnvelope@22, value@22, fields@24, maximum@27, name@27, item@32, derive@51, phrase@51, salt@51, bytes@54, material@55, c@62, key@72, salt@72, seal@72, value@72, bytes@73, iv@76, ciphertext@77, envelope@87, key@87, unseal@87, bytes@90, c@94, c@99, result@102, accountRequest@111, body@111, method@111, path@111, response@112, value@120, filename@126, saveFile@126, type@126, value@126, url@127, link@128
export interface Envelope {
  version: 1;
  salt: string;
  iv: string;
  ciphertext: string;
}
export const VAULT_LIMIT = 8 * 1024 * 1024;
const encoder = new TextEncoder();
const decoder = new TextDecoder('utf-8', { fatal: true });
const context = encoder.encode('applicant-evidence-studio:workspace:v1');

/** Encode bounded bytes in chunks rather than overflowing the argument stack. */
export function base64(bytes: Uint8Array): string {
  let text = '';
  for (let i = 0; i < bytes.length; i += 8192) text += String.fromCharCode(...bytes.subarray(i, i + 8192));
  return btoa(text);
}

/** Validate the envelope BEFORE expensive key derivation or allocation. */
export function validateEnvelope(value: unknown): Envelope {
  if (!value || typeof value !== 'object') throw new Error('Invalid encrypted backup.');
  const fields = value as Record<string, unknown>;
  if (Object.keys(fields).sort().join(',') !== 'ciphertext,iv,salt,version' || fields.version !== 1)
    throw new Error('Unsupported encrypted backup version.');
  for (const [name, maximum] of [
    ['salt', 24],
    ['iv', 16],
    ['ciphertext', 11200000],
  ] as const) {
    const item = fields[name];
    if (typeof item !== 'string' || item.length > maximum || !/^[A-Za-z0-9+/]*={0,2}$/.test(item))
      throw new Error('Invalid encrypted backup.');
  }
  try {
    if (
      atob(fields.salt as string).length !== 16 ||
      atob(fields.iv as string).length !== 12 ||
      atob(fields.ciphertext as string).length < 16 ||
      atob(fields.ciphertext as string).length > VAULT_LIMIT + 16
    )
      throw new Error();
  } catch {
    throw new Error('Invalid encrypted backup.');
  }
  return value as Envelope;
}

/** Derive a non-extractable key; the independent vault phrase never reaches the server. */
export async function derive(phrase: string, salt: string): Promise<CryptoKey> {
  if (phrase.length < 20 || phrase.length > 256)
    throw new Error('Use a unique vault phrase of 20–256 characters, preferably six random words.');
  const bytes = encoder.encode(phrase);
  const material = await crypto.subtle.importKey('raw', bytes, 'PBKDF2', false, ['deriveKey']);
  bytes.fill(0);
  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      hash: 'SHA-256',
      iterations: 600000,
      salt: Uint8Array.from(atob(salt), (c) => c.charCodeAt(0)),
    },
    material,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  );
}

/** A fresh random 96-bit nonce for every save; AAD binds this protocol/version. */
export async function seal(value: unknown, key: CryptoKey, salt: string): Promise<Envelope> {
  const bytes = encoder.encode(JSON.stringify(value));
  if (bytes.length > VAULT_LIMIT)
    throw new Error('Workspace exceeds 8 MiB. Export or remove older records before saving.');
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv, additionalData: context, tagLength: 128 },
    key,
    bytes,
  );
  bytes.fill(0);
  return { version: 1, salt, iv: base64(iv), ciphertext: base64(new Uint8Array(ciphertext)) };
}

/** Authenticate before parsing; wrong keys/corruption return no partially decoded plaintext. */
export async function unseal(envelope: Envelope, key: CryptoKey): Promise<unknown> {
  validateEnvelope(envelope);
  try {
    const bytes = new Uint8Array(
      await crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: Uint8Array.from(atob(envelope.iv), (c) => c.charCodeAt(0)),
          additionalData: context,
          tagLength: 128,
        },
        key,
        Uint8Array.from(atob(envelope.ciphertext), (c) => c.charCodeAt(0)),
      ),
    );
    const result: unknown = JSON.parse(decoder.decode(bytes));
    bytes.fill(0);
    return result;
  } catch {
    throw new Error('Cannot unlock: incorrect vault phrase or damaged backup. No data was replaced.');
  }
}

/** Same-origin cookie requests with anti-CSRF custom header; no bearer secrets in JS storage. */
export async function accountRequest<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch('/vault/' + path, {
    method,
    credentials: 'same-origin',
    cache: 'no-store',
    redirect: 'error',
    headers: { 'Content-Type': 'application/json', 'X-AES-Request': 'v1' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const value = await response.json();
  if (!response.ok) throw new Error(value.detail || 'Account service unavailable.');
  return value as T;
}

/** User-initiated local export only; warn elsewhere that unencrypted report exports are private. */
export function saveFile(value: string, filename: string, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([value], { type }));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
