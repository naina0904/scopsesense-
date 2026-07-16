import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { USER_GUIDE_CHAPTERS } from "../data/userGuideData";

/**
 * Strips markdown symbols for clean, professional PDF typography.
 */
function cleanText(str) {
  if (!str) return "";
  return str
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/`(.*?)`/g, "$1")
    .replace(/_(.*?)_/g, "$1")
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1")
    .trim();
}

/**
 * Generates an official, publication-grade multi-page PDF document
 * of the ScopeSense v2 Enterprise User Guide & Management Manual.
 */
export function generateUserGuidePDF() {
  const doc = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const COLORS = {
    headerBg: [15, 23, 42],       // Slate 900 #0F172A
    headerText: [255, 255, 255],  // White
    accent: [37, 99, 235],        // Blue 600 #2563EB
    title: [15, 23, 42],          // Slate 900
    subtitle: [59, 130, 246],     // Blue 500
    bodyText: [30, 41, 59],       // Slate 800
    subtext: [71, 85, 105],       // Slate 600
    boxBg: [239, 246, 255],       // Blue 50 #EFF6FF
    boxBorder: [59, 130, 246],    // Blue 500
    divider: [226, 232, 240],     // Slate 200
    tableHead: [15, 23, 42],
    tableAlt: [248, 250, 252],
  };

  // ==========================================
  // 1. COVER PAGE & METADATA HEADER
  // ==========================================
  doc.setFillColor(...COLORS.headerBg);
  doc.rect(0, 0, 210, 58, "F");

  doc.setFillColor(...COLORS.accent);
  doc.rect(0, 58, 210, 3, "F");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(26);
  doc.setTextColor(...COLORS.headerText);
  doc.text("SCOPESENSE v2", 20, 28);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(13);
  doc.setTextColor(147, 197, 253);
  doc.text("ENTERPRISE USER GUIDE & MANAGEMENT MANUAL", 20, 42);

  doc.setFontSize(9.5);
  doc.setTextColor(203, 213, 225);
  doc.text("Multi-Agent AI Forensic Audit & Predictive Engineering Intelligence Platform", 20, 51);

  // Metadata Card
  doc.setFillColor(248, 250, 252);
  doc.setDrawColor(...COLORS.divider);
  doc.roundedRect(20, 75, 170, 68, 4, 4, "FD");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(15);
  doc.setTextColor(...COLORS.title);
  doc.text("Document Classification & Technical Specification", 28, 90);

  doc.setDrawColor(...COLORS.divider);
  doc.line(28, 94, 182, 94);

  const metadata = [
    ["Document Type:", "Official Management Manual & Analytical Reference"],
    ["Platform Version:", "ScopeSense v2.4.0-Enterprise (Multi-Agent Architecture)"],
    ["Target Audience:", "Engineering Leads, PMOs, Executive Leadership, Forensic Auditors"],
    ["Date Generated:", new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })],
    ["Security Classification:", "Confidential • Executive & Engineering Team Access Only"],
  ];

  let metaY = 103;
  metadata.forEach(([label, value]) => {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9.5);
    doc.setTextColor(...COLORS.subtext);
    doc.text(label, 28, metaY);

    doc.setFont("helvetica", "normal");
    doc.setTextColor(...COLORS.bodyText);
    doc.text(value, 72, metaY);
    metaY += 7.5;
  });

  // Briefing box below card
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.setTextColor(...COLORS.title);
  doc.text("Executive Briefing & Governance Protocol", 20, 160);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(...COLORS.subtext);
  const briefingText = doc.splitTextToSize(
    "This publication establishes the official operating standards, core Earned Value Management (EVM) calculation formulas, AI confidence thresholds, and multi-agent forensic audit protocols governing ScopeSense v2. Designed for engineering directors and product leaders, it provides immediate 2-sentence diagnostic interpretations, budget leakage isolation rules (Ghost Scope Creep), and step-by-step UI actions across the 7-stage analytical pipeline to guarantee schedule predictability and eliminate project drift.",
    170
  );
  doc.text(briefingText, 20, 168);

  // Bottom footer accent on cover
  doc.setDrawColor(...COLORS.divider);
  doc.line(20, 275, 190, 275);
  doc.setFont("helvetica", "italic");
  doc.setFontSize(8.5);
  doc.setTextColor(148, 163, 184);
  doc.text("ScopeSense v2 Enterprise Documentation • All rights reserved.", 20, 282);

  // ==========================================
  // 2. CHAPTERS & SECTIONS
  // ==========================================
  doc.addPage();
  let cursorY = 25;

  USER_GUIDE_CHAPTERS.forEach((chapter, chIdx) => {
    if (cursorY > 230) {
      doc.addPage();
      cursorY = 25;
    }

    // Chapter Title block
    doc.setFillColor(...COLORS.accent);
    doc.rect(15, cursorY - 5.5, 3.5, 9.5, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(15);
    doc.setTextColor(...COLORS.title);
    doc.text(cleanText(chapter.title), 21.5, cursorY + 1.5);
    cursorY += 10;

    // Chapter Summary block
    if (chapter.summary) {
      doc.setFont("helvetica", "italic");
      doc.setFontSize(10);
      doc.setTextColor(...COLORS.subtext);
      const sumLines = doc.splitTextToSize(cleanText(chapter.summary), 168);
      doc.text(sumLines, 21.5, cursorY);
      cursorY += sumLines.length * 4.5 + 6;
    }

    // Sections loop
    chapter.sections.forEach((section) => {
      if (cursorY > 248) {
        doc.addPage();
        cursorY = 25;
      }

      // Section Heading
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11.5);
      doc.setTextColor(...COLORS.bodyText);
      doc.text(cleanText(section.heading), 21.5, cursorY);
      cursorY += 2;

      doc.setDrawColor(...COLORS.divider);
      doc.line(21.5, cursorY, 188, cursorY);
      cursorY += 6;

      // Check for Markdown Tables vs Text lines
      const rawLines = (section.content || "").split("\n");
      let tableRows = [];
      let inTable = false;

      rawLines.forEach((line) => {
        const trimmed = line.trim();
        if (!trimmed) {
          cursorY += 2;
          return;
        }

        // Detect table line (| cell | cell |)
        if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
          if (trimmed.includes("---")) return; // Skip divider row
          const cells = trimmed
            .split("|")
            .slice(1, -1)
            .map((c) => cleanText(c));
          tableRows.push(cells);
          inTable = true;
          return;
        } else if (inTable && tableRows.length > 0) {
          // Flush accumulated table before continuing
          flushTable(doc, tableRows, COLORS, () => cursorY, (newY) => { cursorY = newY; });
          tableRows = [];
          inTable = false;
        }

        // Bullet point (• or -)
        if (trimmed.startsWith("• ") || trimmed.startsWith("- ")) {
          if (cursorY > 265) {
            doc.addPage();
            cursorY = 25;
          }
          doc.setFont("helvetica", "bold");
          doc.setFontSize(12);
          doc.setTextColor(...COLORS.accent);
          doc.text("•", 23, cursorY + 0.5);

          doc.setFont("helvetica", "normal");
          doc.setFontSize(9.5);
          doc.setTextColor(...COLORS.bodyText);
          const bulletText = cleanText(trimmed.replace(/^[•-]\s+/, ""));
          const textLines = doc.splitTextToSize(bulletText, 158);
          doc.text(textLines, 29, cursorY);
          cursorY += textLines.length * 4.5 + 2.5;
          return;
        }

        // Numbered steps (1. , 2. )
        const numMatch = trimmed.match(/^(\d+\.)\s+(.*)/);
        if (numMatch) {
          if (cursorY > 265) {
            doc.addPage();
            cursorY = 25;
          }
          doc.setFont("helvetica", "bold");
          doc.setFontSize(9.5);
          doc.setTextColor(...COLORS.accent);
          doc.text(numMatch[1], 23, cursorY);

          doc.setFont("helvetica", "normal");
          doc.setFontSize(9.5);
          doc.setTextColor(...COLORS.bodyText);
          const stepText = cleanText(numMatch[2]);
          const textLines = doc.splitTextToSize(stepText, 157);
          doc.text(textLines, 30.5, cursorY);
          cursorY += textLines.length * 4.5 + 2.5;
          return;
        }

        // Callout box (> text)
        if (trimmed.startsWith(">")) {
          if (cursorY > 255) {
            doc.addPage();
            cursorY = 25;
          }
          const calloutText = cleanText(trimmed.replace(/^>\s*/, ""));
          doc.setFont("helvetica", "italic");
          doc.setFontSize(9);
          const calloutLines = doc.splitTextToSize(calloutText, 156);
          const boxHeight = calloutLines.length * 4.5 + 7;

          doc.setFillColor(...COLORS.boxBg);
          doc.roundedRect(21.5, cursorY - 3.5, 166.5, boxHeight, 2, 2, "F");

          doc.setFillColor(...COLORS.boxBorder);
          doc.rect(21.5, cursorY - 3.5, 2.5, boxHeight, "F");

          doc.setTextColor(30, 58, 138);
          doc.text(calloutLines, 27, cursorY + 2);
          cursorY += boxHeight + 4;
          return;
        }

        // Standard paragraph line
        if (cursorY > 268) {
          doc.addPage();
          cursorY = 25;
        }
        doc.setFont("helvetica", "normal");
        doc.setFontSize(9.5);
        doc.setTextColor(...COLORS.bodyText);
        const normalLines = doc.splitTextToSize(cleanText(trimmed), 166.5);
        doc.text(normalLines, 21.5, cursorY);
        cursorY += normalLines.length * 4.5 + 3;
      });

      // If section ended while inside a table, flush it now
      if (inTable && tableRows.length > 0) {
        flushTable(doc, tableRows, COLORS, () => cursorY, (newY) => { cursorY = newY; });
        tableRows = [];
        inTable = false;
      }

      cursorY += 5;
    });

    cursorY += 8;
  });

  // ==========================================
  // 3. RUNNING HEADERS & FOOTERS
  // ==========================================
  const totalPages = doc.internal.getNumberOfPages();
  for (let p = 2; p <= totalPages; p++) {
    doc.setPage(p);

    // Header
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.setTextColor(148, 163, 184);
    doc.text("SCOPESENSE V2 OFFICIAL ENTERPRISE USER GUIDE", 15, 13);

    doc.setFont("helvetica", "normal");
    doc.text("MANAGEMENT REFERENCE MANUAL", 195, 13, { align: "right" });

    doc.setDrawColor(...COLORS.divider);
    doc.line(15, 15.5, 195, 15.5);

    // Footer
    doc.line(15, 281, 195, 281);
    doc.setFontSize(8);
    doc.text("ScopeSense v2 • Multi-Agent Forensic Audit & Predictive Engineering Intelligence", 15, 287);
    doc.text(`Page ${p} of ${totalPages}`, 195, 287, { align: "right" });
  }

  // Trigger download
  doc.save("ScopeSense_v2_Official_User_Manual.pdf");
}

/**
 * Helper to render structured tables via jspdf-autotable
 */
function flushTable(doc, tableRows, COLORS, getCursorY, setCursorY) {
  if (!tableRows || tableRows.length === 0) return;
  const head = [tableRows[0]];
  const body = tableRows.slice(1);

  autoTable(doc, {
    head: head,
    body: body,
    startY: getCursorY() + 2,
    margin: { left: 21.5, right: 22 },
    styles: {
      fontSize: 8.5,
      cellPadding: 3,
      textColor: [30, 41, 59],
      overflow: "linebreak",
    },
    headStyles: {
      fillColor: COLORS.tableHead,
      textColor: [255, 255, 255],
      fontStyle: "bold",
    },
    alternateRowStyles: {
      fillColor: COLORS.tableAlt,
    },
    theme: "grid",
  });

  setCursorY(doc.lastAutoTable.finalY + 8);
}
