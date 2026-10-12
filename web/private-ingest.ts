// Purpose: Jason Stys — bounded document parsing in a disposable, timed browser worker.
// Index: Evidence@3, skills@4, pdfWorker@5, content@8, extractPDF@8, GlobalWorkerOptions@9, getDocument@9, bytes@11, c@11, loading@13, timer@21, pdf@25, pages@27, length@28, i@29, page@30, data@31, item@32, text@32, text@38, _@47, reject@47, content@62, extractPrivate@62, filename@62, result@64, reject@66, resolve@66, worker@67, timer@68, event@74, text@87, proposals@88, label@90, skill@90, i@95, skill@95
import type { Evidence } from './types';
import { skills } from './private-domain';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

/** PDF.js owns a dedicated parser worker; its browser API stays in the window, never a nested worker. */
async function extractPDF(content: string): Promise<{ text: string; warnings: string[] }> {
  const { getDocument, GlobalWorkerOptions } = await import('pdfjs-dist');
  GlobalWorkerOptions.workerSrc = pdfWorker;
  const bytes = Uint8Array.from(atob(content), (c) => c.charCodeAt(0));
  if (!bytes.length || bytes.length > 2000000) throw new Error('Choose a nonempty file up to 2 MB.');
  const loading = getDocument({
    data: bytes,
    useSystemFonts: false,
    disableFontFace: true,
    stopAtErrors: true,
    useWasm: false,
    disableAutoFetch: true,
  });
  let timer: ReturnType<typeof setTimeout>;
  try {
    return await Promise.race([
      (async () => {
        const pdf = await loading.promise;
        if (pdf.numPages > 50) throw new Error('Page limit');
        const pages: string[] = [];
        let length = 0;
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const data = await page.getTextContent();
          const text = data.items.map((item) => ('str' in item ? item.str : '')).join(' ');
          length += text.length;
          if (length > 80000) throw new Error('Text limit');
          pages.push(text);
          page.cleanup();
        }
        const text = pages.join('\n');
        if (!text.trim()) throw new Error('No readable text');
        return {
          text,
          warnings: [
            'PDF reading order may differ. Review tables and the original; scanned images/equations require a supplied text export.',
          ],
        };
      })(),
      new Promise<never>((_, reject) => {
        timer = setTimeout(() => reject(new Error('Parser timeout')), 15000);
      }),
    ]);
  } catch {
    throw new Error(
      'Cannot safely read this document. It may be damaged, encrypted, scanned or beyond size/page limits. Use a UTF-8 text export and review the original.',
    );
  } finally {
    clearTimeout(timer!);
    await loading.destroy();
  }
}

/** Parse locally; no file bytes, text, filename or extracted claims are uploaded. */
export async function extractPrivate(filename: string, content: string) {
  if (content.length > 2700000) throw new Error('Choose a supported file no larger than 2 MB.');
  const result = filename.toLowerCase().endsWith('.pdf')
    ? await extractPDF(content)
    : await new Promise<{ text: string; warnings: string[] }>((resolve, reject) => {
        const worker = new Worker(new URL('./private-parser.worker.ts', import.meta.url), { type: 'module' });
        const timer = window.setTimeout(() => {
          worker.terminate();
          reject(
            new Error('Document parsing exceeded 15 seconds. Paste a professional text export instead.'),
          );
        }, 15000);
        worker.onmessage = (event) => {
          clearTimeout(timer);
          worker.terminate();
          if (event.data.error) reject(new Error(event.data.error));
          else resolve(event.data);
        };
        worker.onerror = () => {
          clearTimeout(timer);
          worker.terminate();
          reject(new Error('Document could not be read safely. Use a text export.'));
        };
        worker.postMessage({ filename, content });
      });
  const text = result.text.toLowerCase();
  const proposals: Evidence[] = Object.entries(skills)
    .filter(
      ([skill, label]) =>
        text.includes(label.toLowerCase()) ||
        new RegExp('(^|[^\\w])' + skill.replaceAll('_', ' ') + '($|[^\\w])').test(text),
    )
    .slice(0, 36)
    .map(([skill], i) => ({
      id: 'proposal_' + i,
      skill,
      kind: 'project',
      level: 'declared',
      summary: 'Mention found in supplied resume; verify its context and your own contribution.',
      source_id: 'resume',
      locator: 'Supplied resume text',
      reviewed: false,
    }));
  return { ...result, filename: filename.slice(0, 240), proposals };
}
