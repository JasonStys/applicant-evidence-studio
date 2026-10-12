// Purpose: Jason Stys — local PDF/DOCX/TXT extraction; no rendering, macros, links or network imports.
// Index: unzipSync@3, value@6, xmlText@6, _@7, code@7, n@9, event@19, warnings@20, content@22, filename@22, bytes@23, c@23, extension@26, text@27, entries@31, expanded@32, files@33, file@34, xml@41, tokens@44, t@46
import { unzipSync } from 'fflate';

/** Decode only fixed XML character entities; never evaluate text as markup or expressions. */
function xmlText(value: string): string {
  return value.replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot|apos);/gi, (_, code: string) => {
    if (code.startsWith('#')) {
      const n = code.toLowerCase().startsWith('#x')
        ? parseInt(code.slice(2), 16)
        : parseInt(code.slice(1), 10);
      return n > 0 && n <= 0x10ffff ? String.fromCodePoint(n) : '�';
    }
    return ({ amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" } as Record<string, string>)[code] || '�';
  });
}

/** Fail explicitly for encrypted/scanned/malformed/oversized documents rather than infer facts. */
self.onmessage = async (event) => {
  const warnings: string[] = [];
  try {
    const { filename, content } = event.data as { filename: string; content: string };
    const bytes = Uint8Array.from(atob(content), (c) => c.charCodeAt(0));
    if (!bytes.length || bytes.length > 2000000)
      throw new Error('Choose a nonempty file no larger than 2 MB.');
    const extension = filename.split('.').pop()?.toLowerCase();
    let text = '';
    if (extension === 'txt' || extension === 'md')
      text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
    else if (extension === 'docx') {
      let entries = 0,
        expanded = 0;
      const files = unzipSync(bytes, {
        filter: (file) => {
          if (++entries > 512 || (expanded += file.originalSize) > 16000000 || file.originalSize > 2000000)
            throw new Error('Document archive exceeds safe extraction limits.');
          return file.name === 'word/document.xml';
        },
      });
      if (!files['word/document.xml']) throw new Error('DOCX main document is missing.');
      const xml = new TextDecoder('utf-8', { fatal: true }).decode(files['word/document.xml']);
      if (/<!DOCTYPE|<!ENTITY/i.test(xml))
        throw new Error('External entities and document type declarations are not supported.');
      const tokens = xml.match(/<w:t(?:\s[^>]*)?>[\s\S]*?<\/w:t>|<\/w:p>|<w:tab\s*\/>/g) || [];
      text = tokens
        .map((t) =>
          t === '</w:p>'
            ? '\n'
            : t.startsWith('<w:tab')
              ? '\t'
              : xmlText(t.replace(/^<w:t(?:\s[^>]*)?>|<\/w:t>$/g, '')),
        )
        .join('');
      warnings.push(
        'Only main-body text is extracted. Check tables, layout, images, equations, headers and footnotes in the original document.',
      );
    } else throw new Error('Supported formats: UTF-8 TXT/MD, text-based PDF, and DOCX.');
    if (!text.trim())
      throw new Error('No readable text found. Supply a text export and review the original.');
    if (text.length > 80000) throw new Error('Extracted text limit exceeded (80,000 characters).');
    self.postMessage({ text, warnings });
  } catch {
    // Parser/library exceptions can contain file text; return a fixed privacy-safe message.
    self.postMessage({
      error:
        'Cannot safely read this document. It may be unsupported, damaged, encrypted, scanned or beyond size/page limits. Use a UTF-8 text export and review the original.',
    });
  }
};
