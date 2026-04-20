"""Tiny web server that renders the 4×8 NeoPixel grid as HTML.
Author: Wolf Paulus <wolf@paulus.com>
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from display import Display
from log import logger

ROWS, COLS = 4, 8

# CSS rgb strings matching NeoDisplay.COLORS indices 0–5, plus off (-1)
CSS_COLORS = [
    "rgb(0, 0, 255)",      # 0: blue    — low/idle
    "rgb(0, 200, 200)",    # 1: cyan    — below normal
    "rgb(0, 255, 0)",      # 2: green   — normal
    "rgb(200, 200, 0)",    # 3: yellow  — above normal
    "rgb(255, 0, 0)",      # 4: red     — high
    "rgb(255, 0, 255)",    # 5: pink    — critical
]
CSS_OFF = "rgb(30, 30, 30)"


class WebDisplay(Display):
    """Display implementation that stores grid state for the web server."""

    def __init__(self, cfg: dict, port: int = 80):
        self._grid = [[(-1, -1)] * COLS for _ in range(ROWS)]
        self._mode = cfg.get("displays", {}).get("neopixel", {}).get("mode", 1)
        self._hosts = [h.get("hostname", "") for h in cfg.get("hosts", [])]
        self._sensors = [s.get("name", "") for s in cfg.get("sensors", {}).values()]
        self._port = port
        self._server = HTTPServer(("", port), _make_handler(self))
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("WebDisplay listening on port %d", port)

    def update(self, hi: int, si: int, values: tuple[int, int]) -> None:
        """Update grid cell. hi=column, si=row (matching NeoDisplay convention)."""
        if 0 <= si < ROWS and 0 <= hi < COLS:
            self._grid[si][hi] = values

    def render(self) -> str:
        """Return an HTML page representing the current grid state."""
        col_headers, row_headers = self._labels()

        # Pad labels to exactly COLS / ROWS so every CSS grid cell is filled
        if col_headers:
            col_headers += [""] * (COLS - len(col_headers))
        if row_headers:
            row_headers += [""] * (ROWS - len(row_headers))

        # Build column header row (with empty top-left corner if row headers exist)
        header_html = ""
        if col_headers:
            if row_headers:
                header_html += '<div class="label corner"></div>\n'
            for label in col_headers:
                header_html += f'<div class="label col-label">{label}</div>\n'

        # Build grid rows
        rows_html = ""
        for row in range(ROWS):
            if row_headers:
                rows_html += f'<div class="label row-label">{row_headers[row]}</div>\n'
            for col in range(COLS):
                value, color_idx = self._grid[row][col]
                css = CSS_COLORS[color_idx] if 0 <= color_idx < len(CSS_COLORS) else CSS_OFF
                tooltip = f"{value}" if value >= 0 else "offline"
                rows_html += f'<div class="led" style="background:{css}" title="{tooltip}"></div>\n'

        grid_cols = COLS + (1 if row_headers else 0)
        return (_HTML
                .replace("{{GRID_COLS}}", str(grid_cols))
                .replace("{{COL_HEADERS}}", header_html)
                .replace("{{ROWS}}", rows_html))

    def _labels(self) -> tuple[list[str], list[str]]:
        """Return (column_headers, row_headers) based on the display mode.
        Mode 1: 1 host × 32 sensors, row-wise fill — no labels
        Mode 2: hosts own rows, sensors own columns
        Mode 3: hosts own columns, sensors own rows
        Mode 4: 32 hosts × 1 sensor, row-wise fill — no labels
        """
        if self._mode == 2:
            return self._sensors[:COLS], self._hosts[:ROWS]
        if self._mode == 3:
            return self._hosts[:COLS], self._sensors[:ROWS]
        return [], []

    def shutdown(self) -> None:
        self._server.shutdown()


def _make_handler(display: WebDisplay):
    """Create a request handler class bound to the given display instance."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = display.render().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass  # suppress default stderr logging

    return Handler


_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ZeroMonitor</title>
<meta http-equiv="refresh" content="10">
<style>
  body {
    margin: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: #111;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, sans-serif;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat({{GRID_COLS}}, auto);
    gap: 6px;
    align-items: center;
    justify-items: center;
  }
  .led {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(255,255,255,0.15);
  }
  .label {
    color: #999;
    font-size: 11px;
    white-space: nowrap;
    padding: 2px 6px;
  }
  .col-label {
    writing-mode: vertical-lr;
    text-align: right;
    min-height: 80px;
  }
  .row-label {
    text-align: right;
  }
  .corner {}
</style>
</head>
<body>
<div class="grid">
{{COL_HEADERS}}
{{ROWS}}
</div>
</body>
</html>
"""
