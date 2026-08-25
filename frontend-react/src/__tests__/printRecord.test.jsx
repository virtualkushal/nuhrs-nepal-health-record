import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// Regression guard for the "blank pages before the record" print bug.
//
// The old strategy hid the app with `visibility: hidden`, which suppresses
// PAINT but keeps LAYOUT — every app wrapper still occupied full page height
// ahead of the record, so the PDF paginated empty pages first. The fix mounts
// PrintableRecord into a dedicated `#print-root` element that is a DIRECT child
// of <body>, letting the print stylesheet COLLAPSE everything else with
// `display: none`. These tests pin down both halves of that contract.

vi.mock("../lib/api.js", () => ({
  api: {
    myBundle: vi.fn(() =>
      Promise.resolve({
        patient: {
          nid: "2345678901",
          full_name: "Ram Bahadur Thapa",
          date_of_birth: "1970-05-12",
          gender: "MALE",
        },
        bundle: { resourceType: "Bundle", type: "collection", entry: [] },
      })
    ),
    listAnnouncements: vi.fn(() => Promise.resolve([])),
  },
}));

import { ToastProvider } from "../context/ToastContext.jsx";
import PatientPortal from "../pages/dashboards/PatientPortal.jsx";

const CSS = readFileSync(resolve(process.cwd(), "src/index.css"), "utf8");

function printBlock() {
  const start = CSS.indexOf("@media print");
  expect(start).toBeGreaterThan(-1);
  // Walk braces to find the matching close of the @media block.
  let depth = 0;
  for (let i = CSS.indexOf("{", start); i < CSS.length; i += 1) {
    if (CSS[i] === "{") depth += 1;
    else if (CSS[i] === "}") {
      depth -= 1;
      if (depth === 0) return CSS.slice(start, i + 1);
    }
  }
  throw new Error("unterminated @media print block");
}

function renderPortal() {
  return render(
    <MemoryRouter>
      <ToastProvider>
        <PatientPortal />
      </ToastProvider>
    </MemoryRouter>
  );
}

afterEach(() => {
  cleanup();
  document.getElementById("print-root")?.remove();
});

describe("printable record mounting", () => {
  it("portals the record into #print-root, a direct child of <body>", async () => {
    const { container } = renderPortal();
    await screen.findAllByText("Ram Bahadur Thapa");

    const printRoot = document.getElementById("print-root");
    expect(printRoot).toBeTruthy();
    expect(printRoot.parentElement).toBe(document.body);

    await waitFor(() => {
      expect(printRoot.querySelector(".print-doc")).toBeTruthy();
    });
    // The record must NOT also live inside the app tree, or the app-collapsing
    // print rule would hide it.
    expect(container.querySelector(".print-doc")).toBeNull();
  });

  it("renders the record header inside the print container", async () => {
    renderPortal();
    const printRoot = await waitFor(() => {
      const el = document.getElementById("print-root");
      expect(el?.querySelector(".print-doc")).toBeTruthy();
      return el;
    });
    expect(printRoot.textContent).toContain("NUHRS — National Health Record");
    expect(printRoot.textContent).toContain("2345678901");
  });

  it("reuses a single #print-root across mounts", async () => {
    const first = renderPortal();
    await waitFor(() => expect(document.getElementById("print-root")).toBeTruthy());
    const node = document.getElementById("print-root");
    first.unmount();

    renderPortal();
    await waitFor(() =>
      expect(document.getElementById("print-root")?.querySelector(".print-doc")).toBeTruthy()
    );
    expect(document.getElementById("print-root")).toBe(node);
    expect(document.querySelectorAll("#print-root")).toHaveLength(1);
  });
});

describe("print stylesheet", () => {
  it("collapses the app instead of hiding it (no visibility tricks)", () => {
    const block = printBlock();
    expect(block).not.toMatch(/visibility/);
    expect(block).toContain("body > *:not(#print-root)");
    expect(block).toMatch(/body > \*:not\(#print-root\)\s*\{\s*display:\s*none\s*!important/);
  });

  it("keeps the record visible and un-offset when printing", () => {
    const block = printBlock();
    expect(block).toMatch(/#print-root\s*\{[^}]*display:\s*block\s*!important/);
    expect(block).toMatch(/#print-root\s*\{[^}]*position:\s*static\s*!important/);
    expect(block).toContain("size: A4");
    expect(block).toMatch(/height:\s*auto\s*!important/);
  });

  it("parks the container off-canvas only on screen", () => {
    // The off-screen offset must live OUTSIDE @media print, otherwise the
    // printed sheet would be shifted off the page.
    const block = printBlock();
    expect(block).not.toContain("-10000px");
    expect(CSS.replace(block, "")).toMatch(/#print-root\s*\{[^}]*left:\s*-10000px/);
  });

  it("no longer styles .print-doc as the off-canvas anchor", () => {
    // `.print-doc` is now purely the document's own class; the positioning
    // contract belongs to #print-root.
    const outsidePrint = CSS.replace(printBlock(), "");
    expect(outsidePrint).not.toMatch(/^\.print-doc\s*\{/m);
  });
});
