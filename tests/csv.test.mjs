import assert from "node:assert/strict";
import test from "node:test";
import { parseBoolean, parseCSV, parseOptionalNumber } from "../assets/js/csv.js";

test("parseCSV handles BOM, quoted commas, and escaped quotes", () => {
  const csv = '\uFEFFid,name,notes\r\n1,"A, B","He said ""yes"""\r\n';
  assert.deepEqual(parseCSV(csv), [
    { id: "1", name: "A, B", notes: 'He said "yes"' },
  ]);
});

test("parseBoolean recognizes explicit public values", () => {
  assert.equal(parseBoolean("TRUE"), true);
  assert.equal(parseBoolean("no"), false);
  assert.equal(parseBoolean("", true), true);
});

test("parseOptionalNumber preserves blank as null", () => {
  assert.equal(parseOptionalNumber(""), null);
  assert.equal(parseOptionalNumber("12.5"), 12.5);
  assert.equal(parseOptionalNumber("not-a-number"), null);
});
