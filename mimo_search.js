// MiMo search helper - reads query from argv, writes JSON payload, calls API.
//
// Configuration: set MIMO_KEY_PATH and MIMO_PAYLOAD_PATH env vars, or defaults
// to .mimo_search_key and _mimo_payload.json in the same directory as this script.
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const query = process.argv[2];
if (!query) {
  console.error('Usage: node mimo_search.js "query"');
  process.exit(1);
}

const scriptDir = __dirname;
const keyPath = process.env.MIMO_KEY_PATH || path.join(scriptDir, '.mimo_search_key');
const payloadFile = process.env.MIMO_PAYLOAD_PATH || path.join(scriptDir, '_mimo_payload.json');

if (!fs.existsSync(keyPath)) {
  console.error(`[error] MiMo key file not found: ${keyPath}`);
  console.error(`[error] Set MIMO_KEY_PATH env var or create the file with your MiMo API key.`);
  process.exit(3);
}

const key = fs.readFileSync(keyPath, 'utf8').trim();

const payload = {
  model: 'mimo-v2.5-pro',
  messages: [
    { role: 'user', content: query }
  ],
  tools: [{ type: 'web_search', web_search: { enable: true, search_query: query } }],
  stream: false
};

fs.writeFileSync(payloadFile, JSON.stringify(payload), 'utf8');

try {
  const out = execSync(
    `curl -s -X POST https://api.xiaomimimo.com/v1/chat/completions ` +
    `-H "api-key: ${key}" ` +
    `-H "Content-Type: application/json" ` +
    `--data-binary @"${payloadFile}"`,
    { maxBuffer: 20 * 1024 * 1024, encoding: 'utf8' }
  );
  try {
    const j = JSON.parse(out);
    if (j.choices && j.choices[0] && j.choices[0].message) {
      console.log(j.choices[0].message.content);
    } else {
      console.log(out);
    }
  } catch (e) {
    console.log(out);
  }
} catch (e) {
  console.error('curl failed:', e.message);
  process.exit(2);
}
