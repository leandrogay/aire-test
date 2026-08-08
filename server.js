const express = require("express");
const multer = require("multer");
const XLSX = require("xlsx");
const path = require("path");
const { computeAnalytics } = require("./analytics");

const app = express();
const PORT = process.env.PORT || 3000;

// Keep uploads in memory — files are parsed and discarded, never written to disk
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 20 * 1024 * 1024 }, // 20 MB cap
});

app.use(express.static(path.join(__dirname, "public")));

const ALLOWED_EXTENSIONS = [".xlsx", ".xls", ".csv"];

app.post("/api/upload", upload.single("file"), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No file received." });
    }

    const ext = path.extname(req.file.originalname).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return res.status(400).json({
        error: `Unsupported file type "${ext}". Upload .xlsx, .xls, or .csv.`,
      });
    }

    const workbook = XLSX.read(req.file.buffer, { type: "buffer" });

    const sheets = workbook.SheetNames.map((name) => {
      const ws = workbook.Sheets[name];
      // header: 1 -> array of arrays; defval keeps empty cells aligned
      const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
      const headers = rows.length ? rows[0].map(String) : [];
      const body = rows.slice(1);
      // Analytics run over the FULL body — must happen before the display cap.
      const analytics = computeAnalytics(headers, body);
      return {
        name,
        headers,
        rowCount: body.length,
        rows: body.slice(0, 1000), // cap what we send to the browser
        analytics,
      };
    });

    res.json({
      filename: req.file.originalname,
      sizeBytes: req.file.size,
      sheets,
    });
  } catch (err) {
    console.error("Parse error:", err);
    res.status(422).json({ error: "Could not parse that file as a spreadsheet." });
  }
});

// Multer errors (e.g. file too large) land here
app.use((err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    return res.status(400).json({ error: `Upload rejected: ${err.message}` });
  }
  next(err);
});

app.listen(PORT, () => {
  console.log(`Sales viewer running at http://localhost:${PORT}`);
});
