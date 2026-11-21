import assert from "node:assert/strict";
import { test } from "node:test";

import onlyCoauthorTrailers from "./only-coauthor-trailers.mjs";

const check = (raw) => onlyCoauthorTrailers({ raw })[0];

test("accepts a single-line message", () => {
  assert.equal(check("feat: add the import tool"), true);
});

test("accepts a header followed by Co-authored-by trailers", () => {
  assert.equal(
    check(
      "fix(ci): pin ruff\n\nCo-authored-by: Someone <someone@example.com>\nCo-authored-by: Other <other@example.com>",
    ),
    true,
  );
});

test("accepts CRLF line endings and a trailing newline", () => {
  assert.equal(check("fix: tidy\r\n\r\nCo-authored-by: Someone <someone@example.com>\r\n"), true);
});

test("ignores blank and comment lines", () => {
  assert.equal(check("chore: tidy\n\n# Please enter the commit message\n#\n"), true);
});

test("rejects a free-form body", () => {
  assert.equal(check("feat: add a manifest\n\nThis adds the second manifest."), false);
});

test("rejects trailers other than Co-authored-by", () => {
  assert.equal(check("feat: add a manifest\n\nSigned-off-by: Someone <someone@example.com>"), false);
});

test("rejects a malformed Co-authored-by trailer", () => {
  assert.equal(check("feat: add a manifest\n\nCo-authored-by: no email here"), false);
});

test("rejects a trailer that is not separated by a blank line", () => {
  assert.equal(check("feat: add a manifest\nCo-authored-by: Someone <someone@example.com>"), false);
});

test("names the offending line in the message", () => {
  const [, message] = onlyCoauthorTrailers({ raw: "feat: x\n\nCloses #12" });
  assert.match(message, /Closes #12/);
});

test("supports the never flavour", () => {
  assert.equal(onlyCoauthorTrailers({ raw: "feat: x\n\nbody" }, "never")[0], true);
});
