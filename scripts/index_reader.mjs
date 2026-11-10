// Purpose: Jason Stys — descriptor-bound, byte-limited UTF-8 reads for source index generation.
// Index: open@3, Buffer@4, INDEX_TEXT_LIMIT@6, limit@9, validateLimit@9, handle@17, limit@17, readIndexHandle@17, info@19, buffer@22, total@23, bytesRead@25, file@34, limit@34, readIndexText@34, handle@36
import { open } from 'node:fs/promises';
import { Buffer } from 'node:buffer';

export const INDEX_TEXT_LIMIT = 2_000_000;

/** Reject invalid budgets before opening a source or allocating its read buffer. */
function validateLimit(limit) {
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > INDEX_TEXT_LIMIT)
    throw new RangeError('Index text limit must be an integer within the supported byte budget.');
}

/** Read only this regular-file descriptor; detect growth beyond limit without path re-resolution.
 * The caller closes the handle. Concurrent in-place writes are not a consistent snapshot.
 */
export async function readIndexHandle(handle, limit = INDEX_TEXT_LIMIT) {
  validateLimit(limit);
  const info = await handle.stat();
  if (!info.isFile()) throw new TypeError('Index input must be a regular file.');
  if (info.size > limit) throw new RangeError('Index input exceeds the byte limit.');
  const buffer = Buffer.alloc(limit + 1);
  let total = 0;
  while (total < buffer.length) {
    const { bytesRead } = await handle.read(buffer, total, buffer.length - total, total);
    if (bytesRead === 0) break;
    total += bytesRead;
  }
  if (total > limit) throw new RangeError('Index input exceeds the byte limit.');
  return new TextDecoder('utf-8', { fatal: true }).decode(buffer.subarray(0, total));
}

/** Open once, inspect/read that descriptor and always close it; propagate every I/O error. */
export async function readIndexText(file, limit = INDEX_TEXT_LIMIT) {
  validateLimit(limit);
  const handle = await open(file, 'r');
  try {
    return await readIndexHandle(handle, limit);
  } finally {
    await handle.close();
  }
}
