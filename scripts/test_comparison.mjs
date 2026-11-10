// Purpose: compile the actual browser comparison domain and run independent Node synthetic oracles.
// File: test_comparison.mjs. Author: Jason Stys. Variables: unique output preserves all prior artifacts.
// Index: build@4, randomUUID@5, spawnSync@6, resolve@7, directory@8, result@18
import { build } from 'vite';
import { randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
const directory = resolve('artifacts', 'comparison-unit-' + randomUUID());
await build({
  configFile: false,
  logLevel: 'warn',
  build: {
    outDir: directory,
    emptyOutDir: false,
    lib: { entry: resolve('web/comparison.ts'), formats: ['es'], fileName: () => 'comparison.js' },
  },
});
const result = spawnSync(process.execPath, ['--test', 'tests/comparison-domain.mjs'], {
  stdio: 'inherit',
  env: { ...process.env, AES_COMPARISON_MODULE: resolve(directory, 'comparison.js') },
});
process.exitCode = result.status ?? 1;
