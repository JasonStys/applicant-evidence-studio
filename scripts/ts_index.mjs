// Purpose: TypeScript compiler AST declaration and variable line maps; generated artifacts are deterministic.
// Index: fs@3, path@4, fileURLToPath@5, ts@6, readIndexText@7, root@8, checking@9, bindings@12, entries@12, file@12, node@12, element@16, entries@21, file@21, node@21, symbols@21, child@35, directory@39, sourceFiles@39, entry@42, files@50, a@60, b@60, report@61, stale@67, filename@68, source@69, file@70, entries@71, sorted@73, a@74, b@74, updated@76, relative@77, entry@88, split@89, document@95, text@96, previousDocument@97, error@100
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
import { readIndexText } from './index_reader.mjs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const checking = process.argv.includes('--check');

/** Record named bindings recursively, including destructured component state variables. */
function bindings(node, file, entries) {
  if (ts.isIdentifier(node))
    entries.add(node.text + '@' + (file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1));
  else if (ts.isObjectBindingPattern(node) || ts.isArrayBindingPattern(node))
    for (const element of node.elements)
      if (ts.isBindingElement(element)) bindings(element.name, file, entries);
}

/** Traverse declarations; locations refer to source, not emitted/minified bundles. */
function symbols(node, file, entries) {
  if ((ts.isImportSpecifier(node) || ts.isImportClause(node) || ts.isNamespaceImport(node)) && node.name)
    bindings(node.name, file, entries);
  if (ts.isVariableDeclaration(node) || ts.isParameter(node) || ts.isBindingElement(node))
    bindings(node.name, file, entries);
  if (
    (ts.isFunctionDeclaration(node) ||
      ts.isClassDeclaration(node) ||
      ts.isInterfaceDeclaration(node) ||
      ts.isTypeAliasDeclaration(node) ||
      ts.isMethodDeclaration(node)) &&
    node.name
  )
    bindings(node.name, file, entries);
  ts.forEachChild(node, (child) => symbols(child, file, entries));
}

/** Walk only project source surfaces, excluding dependencies, runtime data and build output. */
function sourceFiles(directory) {
  return fs
    .readdirSync(directory, { withFileTypes: true })
    .flatMap((entry) =>
      entry.isDirectory()
        ? sourceFiles(path.join(directory, entry.name))
        : /\.(tsx?|mjs)$/.test(entry.name)
          ? [path.join(directory, entry.name)]
          : [],
    );
}
const files = [
  ...sourceFiles(path.join(root, 'web')),
  ...sourceFiles(path.join(root, 'scripts')),
  path.join(root, 'tests/browser.spec.ts'),
  path.join(root, 'tests/private.spec.ts'),
  path.join(root, 'tests/comparison-domain.mjs'),
  path.join(root, 'tests/index-reader.mjs'),
  path.join(root, 'vite.config.ts'),
  path.join(root, 'playwright.config.ts'),
  path.join(root, 'playwright.private.config.ts'),
].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
const report = [
  '# TypeScript / JavaScript declaration and variable map',
  '',
  'Generated with the TypeScript compiler AST. Lexical bindings and named declarations, not dynamic runtime variables.',
  '',
];
const stale = [];
for (const filename of files) {
  const source = await readIndexText(filename);
  const file = ts.createSourceFile(filename, source, ts.ScriptTarget.Latest, true);
  const entries = new Set();
  symbols(file, file, entries);
  const sorted = [...entries].sort(
    (a, b) => Number(a.split('@').at(-1)) - Number(b.split('@').at(-1)) || (a < b ? -1 : a > b ? 1 : 0),
  );
  const updated = source.replace(/^\/\/ Index:.*$/m, '// Index: ' + sorted.join(', '));
  const relative = path.relative(root, filename).replaceAll('\\', '/');
  if (!source.includes('// Index:')) throw new Error('Missing header: ' + relative);
  if (updated !== source) {
    stale.push(relative);
    if (!checking) fs.writeFileSync(filename, updated);
  }
  report.push(
    '## ' + relative,
    '',
    '| Declaration / variable | Line |',
    '| --- | --- |',
    ...sorted.map((entry) => {
      const split = entry.lastIndexOf('@');
      return '| `' + entry.slice(0, split) + '` | ' + entry.slice(split + 1) + ' |';
    }),
    '',
  );
}
const document = path.join(root, 'docs/code-map-typescript.md');
const text = report.join('\n');
let previousDocument = null;
try {
  previousDocument = await readIndexText(document);
} catch (error) {
  // A missing generated report is stale; every other filesystem/encoding failure is an error.
  if (error.code !== 'ENOENT') throw error;
}
if (previousDocument !== text) {
  stale.push('docs/code-map-typescript.md');
  if (!checking) fs.writeFileSync(document, text);
}
if (checking && stale.length) throw new Error('Stale line maps: ' + stale.join(', '));
console.log('TypeScript/JavaScript line maps ' + (checking ? 'checked.' : 'refreshed.'));
