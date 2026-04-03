#!/usr/bin/env bash
# Claude Code hook: auto-format files after Write/Edit
# Applies standard .editorconfig rules using editorconfig-fix.js

set -euo pipefail

export NODE_PATH="$(npm root -g)"

LOGFILE=~/.claude/hooks/format-hook.log
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() { echo "[$(date '+%H:%M:%S')] $1" >> "$LOGFILE"; }

log "--- Hook triggered ---"

# Extract file path from stdin JSON
FILE=$(node -e "
  let d='';
  process.stdin.on('data',c=>d+=c);
  process.stdin.on('end',()=>{
    try{const j=JSON.parse(d);console.log(j.tool_response?.filePath||j.tool_input?.file_path||'')}
    catch(e){console.log('')}
  });
")

log "Extracted file: '${FILE:-<empty>}'"

if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  log "File is empty or does not exist, skipping."
  exit 0
fi

RESULT=$(node "$SCRIPT_DIR/editorconfig-fix.js" "$FILE" 2>&1)

log "Result: $RESULT"

if [[ "$RESULT" == "NO_CONFIG" ]]; then
  log "No .editorconfig found for this file, skipping."
elif [[ "$RESULT" == FIXED:* ]]; then
  log "Applied fixes: ${RESULT#FIXED:}"
elif [[ "$RESULT" == "OK" ]]; then
  log "File already conforms."
else
  log "Unexpected output: $RESULT"
fi

log "Done."
exit 0
