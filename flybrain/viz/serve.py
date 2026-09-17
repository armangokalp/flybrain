"""İzleme panelini yerel olarak sunar (Faz 6).

  /          panel (flybrain/viz/web)
  /kayit/    oturum kaydı (videolar, meta.json, olaylar.json, web/ verileri)

Videolarda ileri geri atlanabilmesi için bayt aralığı istekleri (Range) desteklenir.
Kayıt henüz dışa aktarılmadıysa önce dışa aktarılır (viz/export.py).

Kullanım:
    python -m flybrain.viz.serve runs/oturum-<ad> [--port 8765]
"""

import argparse
import http.server
import mimetypes
import re
import socketserver
from functools import partial
from pathlib import Path
from urllib.parse import unquote

WEB = Path(__file__).with_name("web")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("application/octet-stream", ".bin")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, session: Path, **kw):
        self.session = session
        super().__init__(*args, directory=str(WEB), **kw)

    def translate_path(self, path: str) -> str:
        clean = unquote(path.split("?", 1)[0].split("#", 1)[0])
        if clean.startswith("/kayit/"):
            root = self.session.resolve()
            target = (root / clean[len("/kayit/"):]).resolve()
            if target != root and root not in target.parents:  # kayıt dizininin dışına çıkılamaz
                return str(root / "__yok__")
            return str(target)
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        self._remaining = None
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        path = Path(self.translate_path(self.path))
        if not m or not path.is_file():
            return super().send_head()
        size = path.stat().st_size
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2) or 0))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416)
            return None
        f = path.open("rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(path)))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        self._remaining = None
        while remaining > 0:
            chunk = source.read(min(1 << 16, remaining))
            if not chunk:
                break
            try:
                outputfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                break
            remaining -= len(chunk)

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(session: str | Path, port: int = 8765) -> None:
    session = Path(session).resolve()
    if not (session / "web" / "sahne.json").exists():
        from flybrain.viz.export import export

        print("kayıt dışa aktarılıyor...")
        export(session)
    with Server(("127.0.0.1", port), partial(Handler, session=session)) as httpd:
        print(f"panel: http://127.0.0.1:{port}/  (kayıt: {session})", flush=True)
        httpd.serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kayit")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    serve(args.kayit, args.port)


if __name__ == "__main__":
    main()
