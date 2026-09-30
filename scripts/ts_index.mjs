// Purpose: TypeScript compiler AST declaration and variable line maps; generated artifacts are deterministic.
// Index: fs@3, path@4, fileURLToPath@5, ts@6, root@7, checking@8, bindings@11, entries@11, file@11, node@11, element@15, entries@20, file@20, node@20, symbols@20, child@34, directory@38, sourceFiles@38, entry@41, files@49, a@55, b@55, report@56, stale@62, filename@63, source@64, file@65, entries@66, sorted@68, a@69, b@69, updated@71, relative@72, entry@83, split@84, document@90, text@91
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';
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
  path.join(root, 'vite.config.ts'),
  path.join(root, 'playwright.config.ts'),
].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
const report = [
  '# TypeScript / JavaScript declaration and variable map',
  '',
  'Generated with the TypeScript compiler AST. Lexical bindings and named declarations, not dynamic runtime variables.',
  '',
];
const stale = [];
for (const filename of files) {
  const source = fs.readFileSync(filename, 'utf8');
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
if (!fs.existsSync(document) || fs.readFileSync(document, 'utf8') !== text) {
  stale.push('docs/code-map-typescript.md');
  if (!checking) fs.writeFileSync(document, text);
}
if (checking && stale.length) throw new Error('Stale line maps: ' + stale.join(', '));
console.log('TypeScript/JavaScript line maps ' + (checking ? 'checked.' : 'refreshed.'));
