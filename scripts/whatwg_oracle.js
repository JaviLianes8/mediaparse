// Reads a JSON array of strings on stdin and prints, for each, the serialization that the
// whatwg-mimetype package (the reference implementation of the WHATWG MIME Sniffing
// "parse a MIME type" algorithm) produces, or null when it fails to parse.
// Usage: node scripts/whatwg_oracle.js <folder holding node_modules/whatwg-mimetype>
const path = require("path");
const { MIMEType } = require(path.join(process.argv[2], "node_modules", "whatwg-mimetype"));

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  input += chunk;
});
process.stdin.on("end", () => {
  const out = JSON.parse(input).map((text) => {
    const parsed = MIMEType.parse(text);
    return parsed === null ? null : parsed.toString();
  });
  process.stdout.write(JSON.stringify(out));
});
