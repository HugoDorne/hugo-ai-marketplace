#!/usr/bin/env node
// Applies standard .editorconfig rules to a single file in-place.
// Usage: node editorconfig-fix.js <file-path>

const ec = require('editorconfig');
const fs = require('fs');

const file = process.argv[2];
if (!file) { console.log('NO_FILE'); process.exit(0); }

// editorconfig package needs Windows-style paths on Windows
const winFile = file.replace(/^\/([a-zA-Z])\//, '$1:\\').replace(/\//g, '\\');

(async () => {
  let props;
  try {
    props = await ec.parse(winFile);
  } catch (e) {
    console.log('NO_CONFIG');
    return;
  }

  if (!props || Object.keys(props).length === 0) {
    console.log('NO_CONFIG');
    return;
  }

  let content = fs.readFileSync(file, 'utf8');
  const original = content;
  const changes = [];

  // end_of_line
  if (props.end_of_line) {
    const eol = { lf: '\n', crlf: '\r\n', cr: '\r' }[props.end_of_line];
    if (eol) {
      const fixed = content.replace(/\r\n|\r|\n/g, eol);
      if (fixed !== content) { content = fixed; changes.push('end_of_line'); }
    }
  }

  const eolChar = { lf: '\n', crlf: '\r\n', cr: '\r' }[props.end_of_line] || '\n';

  // trim_trailing_whitespace
  if (props.trim_trailing_whitespace === 'true' || props.trim_trailing_whitespace === true) {
    const lines = content.split(/\r\n|\r|\n/);
    const trimmed = lines.map(l => l.replace(/[\t ]+$/, '')).join(eolChar);
    if (trimmed !== content) { content = trimmed; changes.push('trim_trailing_whitespace'); }
  }

  // indent_style: convert tabs<->spaces
  if (props.indent_style && props.indent_size) {
    const size = parseInt(props.indent_size, 10);
    if (!isNaN(size) && size > 0) {
      const lines = content.split(/\r\n|\r|\n/);
      const converted = lines.map(line => {
        const match = line.match(/^([\t ]*)(.*)/);
        if (!match) return line;
        let indent = match[1];
        const rest = match[2];
        if (props.indent_style === 'space') {
          indent = indent.replace(/\t/g, ' '.repeat(size));
        } else if (props.indent_style === 'tab') {
          const spaces = ' '.repeat(size);
          while (indent.includes(spaces)) indent = indent.replace(spaces, '\t');
        }
        return indent + rest;
      }).join(eolChar);
      if (converted !== content) { content = converted; changes.push('indent_style'); }
    }
  }

  // insert_final_newline
  if (props.insert_final_newline === 'true' || props.insert_final_newline === true) {
    if (content.length > 0 && !content.endsWith('\n') && !content.endsWith('\r')) {
      content += eolChar;
      changes.push('insert_final_newline');
    }
  }

  if (content !== original) {
    fs.writeFileSync(file, content, 'utf8');
    console.log('FIXED:' + changes.join(','));
  } else {
    console.log('OK');
  }
})();
