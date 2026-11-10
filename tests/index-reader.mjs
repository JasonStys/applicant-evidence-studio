// Purpose: Jason Stys — real-filesystem identity, growth, encoding and byte-bound regressions.
// Index: assert@3, mkdtemp@4, open@4, realpath@4, rename@4, rm@4, writeFile@4, os@5, path@6, test@7, INDEX_TEXT_LIMIT@8, readIndexHandle@8, readIndexText@8, fixture@11, run@11, directory@12, actual@16, parent@17, directory@25, empty@26, unicode@27, directory@36, exact@37, excess@38, unicode@39, directory@51, source@52, replacement@53, original@54, handle@58, directory@71, source@72, handle@74, observed@75, requested@76, interleaved@78, stat@79, info@80, buffer@85, length@85, offset@85, position@85, read@85, directory@101, source@102, handle@104, positions@105, chunked@107, buffer@109, length@109, offset@109, position@109, read@109, directory@123, interrupted@126, closedBeforeRead@129, stat@130, info@131, args@135, directory@145, source@146, invalid@153
import assert from 'node:assert/strict';
import { mkdtemp, open, realpath, rename, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { INDEX_TEXT_LIMIT, readIndexHandle, readIndexText } from '../scripts/index_reader.mjs';

/** Create an unrelated private fixture directory and delete only its exact owned path. */
async function fixture(run) {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'aes-index-reader-'));
  try {
    await run(directory);
  } finally {
    const actual = await realpath(directory);
    const parent = await realpath(os.tmpdir());
    if (path.dirname(actual) !== parent || !path.basename(actual).startsWith('aes-index-reader-'))
      throw new Error('Fixture cleanup target left its owned temporary directory.');
    await rm(actual, { recursive: true, force: true });
  }
}

test('empty and multibyte sources round-trip without rewriting bytes', async () => {
  await fixture(async (directory) => {
    const empty = path.join(directory, 'empty.txt');
    const unicode = path.join(directory, 'unicode.txt');
    await writeFile(empty, '', { flag: 'wx' });
    await writeFile(unicode, 'source µV 温度\n', { flag: 'wx' });
    assert.equal(await readIndexText(empty), '');
    assert.equal(await readIndexText(unicode), 'source µV 温度\n');
  });
});

test('exact byte limit is included; an extra byte and split UTF-8 character are rejected', async () => {
  await fixture(async (directory) => {
    const exact = path.join(directory, 'exact.txt');
    const excess = path.join(directory, 'excess.txt');
    const unicode = path.join(directory, 'unicode.txt');
    await writeFile(exact, 'x'.repeat(INDEX_TEXT_LIMIT), { flag: 'wx' });
    await writeFile(excess, 'x'.repeat(INDEX_TEXT_LIMIT + 1), { flag: 'wx' });
    await writeFile(unicode, 'µ', { flag: 'wx' });
    assert.equal((await readIndexText(exact)).length, INDEX_TEXT_LIMIT);
    await assert.rejects(readIndexText(excess), RangeError);
    await assert.rejects(readIndexText(unicode, 1), RangeError);
    assert.equal(await readIndexText(unicode, 2), 'µ');
  });
});

test('opened identity survives replacement of its original pathname', async () => {
  await fixture(async (directory) => {
    const source = path.join(directory, 'source.txt');
    const replacement = path.join(directory, 'replacement.txt');
    const original = path.join(directory, 'original.txt');
    await writeFile(source, 'original descriptor', { flag: 'wx' });
    await writeFile(replacement, 'replacement pathname', { flag: 'wx' });
    await assert.rejects(writeFile(replacement, 'do not clobber', { flag: 'wx' }), { code: 'EEXIST' });
    const handle = await open(source, 'r');
    try {
      await rename(source, original);
      await rename(replacement, source);
      assert.equal(await readIndexHandle(handle), 'original descriptor');
      assert.equal(await readIndexText(source), 'replacement pathname');
    } finally {
      await handle.close();
    }
  });
});

test('real growth after fstat cannot bypass the bounded read', async () => {
  await fixture(async (directory) => {
    const source = path.join(directory, 'growth.txt');
    await writeFile(source, 'small', { flag: 'wx' });
    const handle = await open(source, 'r+');
    let observed = 0;
    let requested = 0;
    try {
      const interleaved = {
        async stat() {
          const info = await handle.stat();
          observed = info.size;
          await handle.write(Buffer.from('x'.repeat(64)), 0, 64, info.size);
          return info;
        },
        read(buffer, offset, length, position) {
          requested += length;
          return handle.read(buffer, offset, length, position);
        },
      };
      await assert.rejects(readIndexHandle(interleaved, 32), RangeError);
      assert.equal(observed, 5);
      assert.equal(requested, 33);
      assert.equal((await handle.stat()).size, 69);
    } finally {
      await handle.close();
    }
  });
});

test('partial reads continue at explicit positions instead of dropping evidence', async () => {
  await fixture(async (directory) => {
    const source = path.join(directory, 'partial.txt');
    await writeFile(source, 'abcdef', { flag: 'wx' });
    const handle = await open(source, 'r');
    const positions = [];
    try {
      const chunked = {
        stat: () => handle.stat(),
        read(buffer, offset, length, position) {
          positions.push(position);
          return handle.read(buffer, offset, Math.min(length, 2), position);
        },
      };
      assert.equal(await readIndexHandle(chunked, 6), 'abcdef');
      assert.deepEqual(positions, [0, 2, 4, 6]);
    } finally {
      await handle.close();
    }
  });
});

test('missing, nonregular and interrupted reads fail rather than become empty evidence', async () => {
  await fixture(async (directory) => {
    await assert.rejects(readIndexText(path.join(directory, 'missing.txt')), { code: 'ENOENT' });
    await assert.rejects(readIndexText(directory));
    const interrupted = await open(path.join(directory, 'interrupted.txt'), 'wx+');
    await interrupted.writeFile('source');
    try {
      const closedBeforeRead = {
        async stat() {
          const info = await interrupted.stat();
          await interrupted.close();
          return info;
        },
        read: (...args) => interrupted.read(...args),
      };
      await assert.rejects(readIndexHandle(closedBeforeRead), { code: 'EBADF' });
    } finally {
      await interrupted.close();
    }
  });
});

test('malformed UTF-8 is rejected before the indexer can rewrite a source', async () => {
  await fixture(async (directory) => {
    const source = path.join(directory, 'invalid.txt');
    await writeFile(source, Buffer.from([0xc3, 0x28]), { flag: 'wx' });
    await assert.rejects(readIndexText(source), TypeError);
  });
});

test('invalid budgets reject before file access', async () => {
  for (const invalid of [0, -1, 1.5, NaN, Infinity, INDEX_TEXT_LIMIT + 1])
    await assert.rejects(readIndexText('missing-but-never-opened', invalid), RangeError);
});
