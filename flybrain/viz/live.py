"""Canlı izleme: simülasyon sürerken sineği tarayıcıdan seyretmek (Faz 6'nın kalanı, Z-28).

Kayıttan oynatma (viz/serve.py) bittikten sonra izlemeyi sağlıyor; bu modül **oturum sürerken**
bakmayı sağlıyor. Sinek her adımda çizilmiyor: her `every_ms` simülasyon milisaniyesinde bir kare
alınıp JPEG olarak yerel bir sunucuya konuyor, tarayıcı da onu akış olarak gösteriyor.

**Ağır çekim.** Kapalı döngü gerçek zamanın ~3 katı yavaş (Z-21). Yayın da o hızda akar; karenin
üstünde ölçülen anlık hız yazıyor ("ağır çekim ~0,3×"). Hiçbir şey hızlandırılmıyor.

Sunucu yalnızca 127.0.0.1'de dinler.
"""

import io
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import mujoco as mj
import numpy as np
from PIL import Image, ImageDraw

from flybrain.viz.video import _font

PORT = 8766
BOUNDARY = "flybrain"

PAGE = """<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>flybrain — canlı</title>
<style>html,body{margin:0;background:#0f1012;color:#e8e8ea;font:14px system-ui,sans-serif;
height:100%;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:10px}
img{max-width:96vw;max-height:84vh;border-radius:10px}
button{background:#23252a;color:#e8e8ea;border:1px solid #3a3d44;border-radius:8px;
padding:7px 16px;font:inherit;cursor:pointer}button:hover{background:#2c2f35}
.alt{color:#9a9aa4}</style></head>
<body><img src="/akis" alt="canlı">
<div><button id="d" onclick="duraklat()">duraklat</button>
<span class="alt">&nbsp; sinek gerçek zamandan yavaş yaşıyor; hız karenin üstünde</span></div>
<script>async function duraklat(){const r=await fetch('/duraklat',{method:'POST'});
const j=await r.json();document.getElementById('d').textContent=j.duraklatildi?'devam et':'duraklat';}
</script></body></html>"""


class LiveStream:
    """Sineği çizip yerel bir sunucuya akıtır; `fly.on_step` ile beslenir."""

    def __init__(self, fly, width: int = 720, height: int = 540, every_ms: float = 50.0,
                 port: int = PORT, quality: int = 70):
        self.fly = fly
        self.every_ms = every_ms
        self.quality = quality
        self.jpeg: bytes | None = None
        self.note = ""
        self.browser: np.ndarray | None = None  # tarayıcının son karesi (kaydırma, animasyon)
        self.paused = False  # izleyici sayfadan duraklatabilir
        self._next_ms = 0.0
        self._lock = threading.Lock()
        self._wall0 = time.perf_counter()
        self._sim0 = fly.brain.time_ms
        self._speed = 0.0
        self.renderer = mj.Renderer(fly.body.sim.mj_model, height, width)
        if fly.scene is not None:
            fly.scene.register(self.renderer)  # telefon ekranı bu çiziciye de yüklensin
        self.camera = mj.MjvCamera()
        self.camera.type = mj.mjtCamera.mjCAMERA_FREE
        self.camera.distance, self.camera.elevation = 9.0, -14.0
        self._thorax = mj.mj_name2id(fly.body.sim.mj_model, mj.mjtObj.mjOBJ_BODY,
                                     f"{fly.body.fly.name}/c_thorax")
        self._screen = mj.mj_name2id(fly.body.sim.mj_model, mj.mjtObj.mjOBJ_BODY, "ekran")
        self.font, self.small = _font(20), _font(15)
        self.server = ThreadingHTTPServer(("127.0.0.1", port), _handler(self))
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        fly.on_step = self.step

    # ---- çizim ----

    def _frame(self) -> np.ndarray:
        d = self.fly.body.sim.mj_data
        ahead = d.xpos[self._screen][:2] - d.xpos[self._thorax][:2]
        self.camera.azimuth = float(np.degrees(np.arctan2(ahead[1], ahead[0])) + 32.0)
        self.camera.lookat[:] = d.xpos[self._thorax]
        self.renderer.update_scene(d, self.camera)
        return self.renderer.render()

    def _panels(self, sahne: np.ndarray) -> Image.Image:
        """3B sahne + sineğin gözleri + gerçek tarayıcı, tek karede.

        Tarayıcı paneli, sineğin **görmediği** şeyi gösterir: asıl kaydırma perde arkasında
        olur (sineğin ekranı solarak geçer, Z-35), beğeni animasyonu da orada oynar.
        """
        sol = Image.fromarray(sahne)
        sag_w = 300
        tuval = Image.new("RGB", (sol.width + sag_w + 18, sol.height), (15, 16, 18))
        tuval.paste(sol, (0, 0))
        x, y = sol.width + 12, 0
        eyes = self.fly.eyes.last_frames if self.fly.eyes is not None else {}
        if eyes:
            goz = np.concatenate([eyes["L"], eyes["R"]], axis=1)
            g = Image.fromarray(goz)
            g = g.resize((sag_w, max(1, round(g.height * sag_w / g.width))), Image.BILINEAR)
            tuval.paste(g, (x, y + 16))
            ImageDraw.Draw(tuval).text((x, y), "sineğin gözleri", fill=(150, 150, 160), font=self.small)
            y += g.height + 26
        if self.browser is not None:
            b = Image.fromarray(self.browser)
            kalan = sol.height - y - 20
            b = b.resize((max(1, round(b.width * kalan / b.height)), kalan), Image.BILINEAR)
            tuval.paste(b, (x, y + 16))
            ImageDraw.Draw(tuval).text((x, y), "tarayıcı (sinek bunu görmüyor)",
                                       fill=(150, 150, 160), font=self.small)
        return tuval

    def _draw(self, img: np.ndarray) -> bytes:
        pil = self._panels(img)
        d = ImageDraw.Draw(pil)
        t_s = self.fly.brain.time_ms / 1000.0
        label = f"{t_s:6.2f} sn  ·  " + (f"ağır çekim {self._speed:.2f}×" if self._speed < 0.95
                                         else f"{self._speed:.2f}×")
        d.rectangle([0, 0, pil.width, 30], fill=(15, 16, 18))
        d.text((10, 6), label, fill=(232, 232, 234), font=self.font)
        if self.note:
            d.rectangle([0, pil.height - 26, pil.width, pil.height], fill=(15, 16, 18))
            d.text((10, pil.height - 22), self.note[:90], fill=(200, 200, 210), font=self.small)
        if self.fly.held:
            d.text((pil.width - 210, 6), "deneyci tutuyor", fill=(255, 190, 90), font=self.small)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=self.quality)
        return buf.getvalue()

    # ---- besleme ----

    def step(self, fly) -> None:
        while self.paused:  # izleyici sayfadan duraklattı: simülasyon burada bekler
            time.sleep(0.05)
            self._wall0 += 0.05  # bekleme ölçülen hıza girmesin
        t = fly.brain.time_ms
        if t < self._next_ms:
            return
        self._next_ms = t + self.every_ms
        wall = time.perf_counter() - self._wall0
        if wall > 0.5:
            self._speed = (t - self._sim0) / 1000.0 / wall
        jpeg = self._draw(self._frame())
        with self._lock:
            self.jpeg = jpeg

    def say(self, note: str) -> None:
        """Karenin altındaki satır (post, karar, eylem)."""
        self.note = note

    def show_browser(self, shot: np.ndarray) -> None:
        """Tarayıcının son karesi (kaydırma sırasında ve eylemden sonra beslenir)."""
        self.browser = shot

    def latest(self) -> bytes | None:
        with self._lock:
            return self.jpeg

    def close(self) -> None:
        self.fly.on_step = None
        self.server.shutdown()
        self.server.server_close()
        self.renderer.close()


def _handler(stream: LiveStream):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):  # sessiz
            pass

        def handle_one_request(self):
            try:
                super().handle_one_request()
            except (ConnectionResetError, BrokenPipeError):  # izleyici sekmeyi kapattı
                self.close_connection = True

        def do_POST(self):
            if self.path != "/duraklat":
                self.send_error(404)
                return
            stream.paused = not stream.paused
            body = f'{{"duraklatildi": {str(stream.paused).lower()}}}'.encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                body = PAGE.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path != "/akis":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={BOUNDARY}")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            son = None
            try:
                while True:
                    jpeg = stream.latest()
                    if jpeg is None or jpeg is son:
                        time.sleep(0.03)
                        continue
                    son = jpeg
                    self.wfile.write(f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\n"
                                     f"Content-Length: {len(jpeg)}\r\n\r\n".encode())
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass

    return Handler
