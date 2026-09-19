// flybrain oturum paneli (Faz 6): kaydedilmiş bir oturumu senkron görünümlerle oynatır.
// Veriler /kayit/ altından gelir (viz/serve.py); biçim: viz/record.py ve viz/export.py.

import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);

const KAYIT = '/kayit/';
const $ = (id) => document.getElementById(id);
// Kayıttaki adlar Türkçe (kod içi); panel İngilizce gösterir.
const EYLEM = {
  ileri: ['next post', '--ileri'],
  geri: ['previous post', '--geri'],
  begen: ['like', '--begen'],
  kaydet: ['save', '--begen'],
  yorum: ['comment', '--yorum'],
  takip: ['follow', '--takip'],
  cikis: ['escape', '--cikis'],
  sekme_sol: ['switch tab (left)', '--sekme'],
  sekme_sag: ['switch tab (right)', '--sekme'],
  timar: ['grooming', '--timar'],
  ilgi_kaybi: ['lost interest', '--ilgi'],
};
const KANAL_ADI = {
  ileri: 'leg motor neurons', geri: 'backward walking command neurons (MDN)',
  hortum: 'proboscis motor neurons', yorum: 'wing steering motor neurons',
  takip: 'abdomen motor neurons', cikis: 'escape descending neurons',
  sekme: 'neck motor neurons', timar: 'front leg motor neurons',
};
const KANAL_KISA = {
  ileri: 'walk', geri: 'walk backward', hortum: 'proboscis', yorum: 'wings',
  takip: 'abdomen', cikis: 'escape', sekme: 'head turn', timar: 'grooming',
};
// Kayıttaki gerekçe metinleri (motor/selector.py, body/viewer.py) İngilizceye.
function reason(s) {
  if (!s) return '';
  return s
    .replace(/^hiçbir kanal eşiği aşmadı$/, 'no channel crossed its threshold')
    .replace(/^kaçış döngüsü: (\d+) nöbet boyunca çıkıştan başka karar yok$/, 'escape loop: $1 bouts with no decision other than escape')
    .replace(/^(\w+): z=/, (m, ch) => `${KANAL_KISA[ch] ?? ch}: z=`)
    .replace(/ > eşik /, ' > threshold ')
    .replace(/; kaydetme eşiği ([\d.-]+) de aşıldı/, '; also above the save threshold $1');
}
// Kas adları: "hortum:x", "boyun:sol", "kanat:sag:x", "karin:sol", "lf:x".
const PARCA = { hortum: 'proboscis', boyun: 'neck', kanat: 'wing', karin: 'abdomen', sol: 'left', sag: 'right' };
const kasAdi = (name) => name.split(':').map((w) => PARCA[w] ?? w).join(':');
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const sn = (ms) => (ms / 1000).toFixed(2) + ' s';

async function getJSON(path) {
  const r = await fetch(KAYIT + path);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

async function getBin(path, Type) {
  const r = await fetch(KAYIT + 'web/' + path);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return new Type(await r.arrayBuffer());
}

// ---------------------------------------------------------------- sinek görünümü

function checker() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) {
    g.fillStyle = (i + j) % 2 ? '#3a3c40' : '#2e3034';
    g.fillRect(i * 32, j * 32, 32, 32);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(40, 40);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

class FlyView {
  constructor(canvas, scene, geo, frames, screenVideo, onPick) {
    this.canvas = canvas;
    this.scene = scene;
    this.frames = frames;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(2, devicePixelRatio));
    this.world = new THREE.Scene();
    this.world.background = new THREE.Color(0x15171a);
    this.camera = new THREE.PerspectiveCamera(35, 1, 0.05, 500);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.08;  // kamera zeminin altına inmesin
    this.world.add(new THREE.HemisphereLight(0xffffff, 0x303030, 1.6));
    const sun = new THREE.DirectionalLight(0xffffff, 1.8);
    sun.position.set(3, -4, 8);
    this.world.add(sun);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(80, 80),
      new THREE.MeshStandardMaterial({ map: checker(), roughness: 1 }));
    this.world.add(floor);

    const screenTex = new THREE.VideoTexture(screenVideo);
    screenTex.colorSpace = THREE.SRGBColorSpace;
    screenTex.flipY = false;
    this.meshes = scene.parcalar.map((p) => {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(geo.kose.subarray(p.kose[0] * 3, (p.kose[0] + p.kose[1]) * 3), 3));
      g.setIndex(new THREE.BufferAttribute(geo.yuz.subarray(p.yuz[0], p.yuz[0] + p.yuz[1]), 1));
      if (p.uv) g.setAttribute('uv', new THREE.BufferAttribute(geo.uv.subarray(p.uv[0] * 2, (p.uv[0] + p.uv[1]) * 2), 2));
      g.computeVertexNormals();
      const [r, gg, b, a] = p.renk;
      const mat = p.doku
        ? new THREE.MeshBasicMaterial({ map: screenTex, side: THREE.DoubleSide })
        : new THREE.MeshStandardMaterial({
          color: new THREE.Color().setRGB(r, gg, b, THREE.SRGBColorSpace),
          transparent: a < 1, opacity: a, depthWrite: a >= 1, roughness: 0.65, side: THREE.DoubleSide,
        });
      const mesh = new THREE.Mesh(g, mat);
      mesh.userData = p;
      this.world.add(mesh);
      return mesh;
    });
    this.thorax = scene.parcalar.findIndex((p) => p.govde.endsWith('/c_thorax'));
    this.screen = scene.parcalar.findIndex((p) => p.doku === 'ekran');
    this.lastThorax = null;
    // Kamera sineğin arkasında ve yanında: telefon ekranı sineğin önünde görünür.
    const at = (j) => new THREE.Vector3(frames[j * 7], frames[j * 7 + 1], frames[j * 7 + 2]);
    const ahead = at(this.screen).sub(at(this.thorax)).setZ(0).normalize();
    const side = new THREE.Vector3(-ahead.y, ahead.x, 0);
    this.camera.position.copy(ahead.multiplyScalar(-4.2).add(side.multiplyScalar(3.2))).setZ(2.6);
    this.picked = [];

    const ray = new THREE.Raycaster();
    let down = null;
    canvas.addEventListener('pointerdown', (e) => { down = [e.clientX, e.clientY]; });
    canvas.addEventListener('pointerup', (e) => {
      if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
      const rect = canvas.getBoundingClientRect();
      const ndc = new THREE.Vector2(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
      ray.setFromCamera(ndc, this.camera);
      const hit = ray.intersectObjects(this.meshes.filter((m) => m.userData.tur === 'sinek'))[0];
      onPick(hit ? hit.object.userData : null);
    });
  }

  highlight(bodies) {
    for (const m of this.meshes) {
      if (m.userData.tur !== 'sinek') continue;
      const on = bodies.has(m.userData.kasli);
      m.material.emissive?.set(on ? 0xc08000 : 0x000000);
    }
  }

  setTime(t) {
    const f = this.scene.kare;
    const i = Math.max(0, Math.min(f.sayi - 1, Math.round((t - f.t_ms[0]) / f.adim_ms)));
    const G = this.meshes.length;
    const a = this.frames;
    for (let j = 0; j < G; j++) {
      const o = (i * G + j) * 7;
      const m = this.meshes[j];
      m.position.set(a[o], a[o + 1], a[o + 2]);
      m.quaternion.set(a[o + 4], a[o + 5], a[o + 6], a[o + 3]);
    }
    const th = this.meshes[this.thorax].position;
    if (!this.lastThorax) {
      this.controls.target.copy(th);
      this.camera.position.add(th);
    } else {
      const delta = th.clone().sub(this.lastThorax);
      this.camera.position.add(delta);
      this.controls.target.add(delta);
    }
    this.lastThorax = th.clone();
    return this.scene.tutuluyor[i] === 1;
  }

  render() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    if (this.canvas.width !== Math.round(w * this.renderer.getPixelRatio())) {
      this.renderer.setSize(w, h, false);
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
    }
    this.controls.update();
    this.renderer.render(this.world, this.camera);
  }
}

// ---------------------------------------------------------------- beyin görünümü

const SINIF_GRUBU = [
  ['vision (optic lobe)', '#3987e5', (c) => c.startsWith('ol_') || c.startsWith('visual')],
  ['central brain', '#199e70', (c) => c === 'cb_intrinsic'],
  ['nerve cord', '#9085e9', (c) => c === 'vnc_intrinsic'],
  ['sensory', '#c98500', (c) => c.includes('sensory')],
  ['descending / ascending', '#d55181', (c) => c.startsWith('descending') || c.startsWith('ascending') || c.includes('_ascending') || c.includes('_descending')],
  ['motor', '#e66767', (c) => c.includes('motor') || c.includes('efferent')],
  ['other', '#8a8a80', () => true],
];
const TAU_MS = 60;
const BASE = 0.32;  // taban katmanında nöronun parlaklığı (sınıf rengine göre)

class BrainView {
  constructor(canvas, info, pos, cls, approx, spikes) {
    this.canvas = canvas;
    this.n = info.sayi;
    this.spikes = spikes;
    this.approx = approx;
    this.showApprox = true;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
    this.renderer.setPixelRatio(Math.min(2, devicePixelRatio));
    this.world = new THREE.Scene();
    this.world.background = new THREE.Color(0x0d0e10);
    this.camera = new THREE.PerspectiveCamera(30, 1, 1, 20000);
    // MaleCNS'te z ekseni beyinden sinir kordonuna uzanıyor: beyin üstte görünsün diye yukarı −z.
    // Kamera y ekseni üzerinde. Yukarı yön denetimden önce ayarlanmalı.
    this.camera.up.set(0, 0, -1);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;

    const groupOf = info.siniflar.map((c) => SINIF_GRUBU.findIndex(([, , f]) => f(c)));
    this.base = new Float32Array(this.n * 3);
    const tmp = new THREE.Color();
    const rgb = SINIF_GRUBU.map(([, hex]) => tmp.set(hex).toArray());
    for (let i = 0; i < this.n; i++) {
      const c = rgb[groupOf[cls[i]]];
      this.base.set(c, i * 3);
    }
    this.level = new Float32Array(this.n);
    this.pos = pos;
    // Taban katmanı: bütün nöronlar, sönük sınıf rengiyle.
    this.color = new Float32Array(this.n * 3);
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    this.colorAttr = new THREE.BufferAttribute(this.color, 3);
    geom.setAttribute('color', this.colorAttr);
    geom.computeBoundingSphere();
    this.world.add(new THREE.Points(geom, new THREE.PointsMaterial({ size: 1.4, sizeAttenuation: false, vertexColors: true })));
    this.paintBase();
    // Ateşleyen katman: yakın zamanda spike atan nöronlar, önde ve parlak.
    this.hotPos = new Float32Array(this.n * 3);
    this.hotColor = new Float32Array(this.n * 3);
    this.hotGeom = new THREE.BufferGeometry();
    this.hotPosAttr = new THREE.BufferAttribute(this.hotPos, 3).setUsage(THREE.DynamicDrawUsage);
    this.hotColorAttr = new THREE.BufferAttribute(this.hotColor, 3).setUsage(THREE.DynamicDrawUsage);
    this.hotGeom.setAttribute('position', this.hotPosAttr);
    this.hotGeom.setAttribute('color', this.hotColorAttr);
    this.hotGeom.boundingSphere = geom.boundingSphere;
    this.world.add(new THREE.Points(this.hotGeom, new THREE.PointsMaterial({
      size: 2.2, sizeAttenuation: false, vertexColors: true, transparent: true,
      blending: THREE.AdditiveBlending, depthTest: false, depthWrite: false,
    })));

    this.markGeom = new THREE.BufferGeometry();
    this.mark = new THREE.Points(this.markGeom, new THREE.PointsMaterial({
      size: 5, sizeAttenuation: false, color: 0xf0b429, transparent: true, opacity: 0.9,
      depthTest: false, depthWrite: false,
    }));
    this.mark.renderOrder = 2;
    this.world.add(this.mark);

    const s = geom.boundingSphere;
    this.controls.target.copy(s.center);
    this.camera.position.set(s.center.x, s.center.y - s.radius * 3.4, s.center.z);
    this.shown = null;

    $('lejant').innerHTML = SINIF_GRUBU.map(([ad, hex]) => `<span><i style="background:${hex}"></i>${ad}</span>`).join('');
    $('beyin-not').textContent = `${info.sayi.toLocaleString('en-US')} neurons at their cell body positions · ${info.yaklasik_sayi.toLocaleString('en-US')} approximate`;
  }

  markNeurons(idx) {
    const p = new Float32Array(idx.length * 3);
    idx.forEach((n, k) => p.set(this.pos.subarray(n * 3, n * 3 + 3), k * 3));
    this.markGeom.setAttribute('position', new THREE.BufferAttribute(p, 3));
    this.markGeom.computeBoundingSphere();
  }

  addSpikes(a, b, weight) {
    const { ofset, noron } = this.spikes;
    const lo = Math.max(0, a), hi = Math.min(ofset.length - 1, b);
    for (let ms = lo; ms < hi; ms++) {
      const w = weight ? weight(ms) : 1;
      for (let k = ofset[ms]; k < ofset[ms + 1]; k++) this.level[noron[k]] += w;
    }
  }

  setTime(t) {
    const now = Math.floor(t);
    if (this.shown === null || now < this.shown || now - this.shown > 300) {
      this.level.fill(0);
      this.addSpikes(now - 5 * TAU_MS, now, (ms) => Math.exp(-(now - ms) / TAU_MS));
    } else if (now > this.shown) {
      const decay = Math.exp(-(now - this.shown) / TAU_MS);
      for (let i = 0; i < this.n; i++) this.level[i] *= decay;
      this.addSpikes(this.shown, now);
    }
    this.shown = now;
    const L = this.level, A = this.approx, P = this.pos, HP = this.hotPos, HC = this.hotColor;
    let m = 0;
    for (let i = 0; i < this.n; i++) {
      const v = L[i];
      if (v < 0.03 || (!this.showApprox && A[i])) continue;
      const w = Math.min(1, v);
      HP[m * 3] = P[i * 3]; HP[m * 3 + 1] = P[i * 3 + 1]; HP[m * 3 + 2] = P[i * 3 + 2];
      HC[m * 3] = w; HC[m * 3 + 1] = 0.8 * w; HC[m * 3 + 2] = 0.45 * w;
      m++;
    }
    this.hotGeom.setDrawRange(0, m);
    this.hotPosAttr.addUpdateRange(0, m * 3);
    this.hotColorAttr.addUpdateRange(0, m * 3);
    this.hotPosAttr.needsUpdate = true;
    this.hotColorAttr.needsUpdate = true;
  }

  paintBase() {
    const B = this.base, C = this.color, A = this.approx;
    for (let i = 0; i < this.n; i++) {
      const k = (this.showApprox || !A[i]) ? BASE : 0;
      C[i * 3] = B[i * 3] * k; C[i * 3 + 1] = B[i * 3 + 1] * k; C[i * 3 + 2] = B[i * 3 + 2] * k;
    }
    this.colorAttr.needsUpdate = true;
  }

  render() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    if (this.canvas.width !== Math.round(w * this.renderer.getPixelRatio())) {
      this.renderer.setSize(w, h, false);
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
    }
    this.controls.update();
    this.renderer.render(this.world, this.camera);
  }
}

// ---------------------------------------------------------------- geriye izleme

function countSpikes(spikes, idx, a, b) {
  const want = new Map(idx.map((n) => [n, 0]));
  const { ofset, noron } = spikes;
  for (let ms = Math.max(0, a); ms < Math.min(ofset.length - 1, b); ms++) {
    for (let k = ofset[ms]; k < ofset[ms + 1]; k++) {
      const n = noron[k];
      if (want.has(n)) want.set(n, want.get(n) + 1);
    }
  }
  return want;
}

function traceTable(rows) {
  const body = $('iz-tablo').tBodies[0];
  const max = Math.max(1, ...rows.filter((r) => !r.grup).map((r) => r.sayi));
  body.innerHTML = rows.map((r) => r.grup
    ? `<tr class="grup"><td colspan="3">${r.grup}</td></tr>`
    : `<tr><td>${r.ad}</td><td style="width:40%"><div class="cubuk" style="width:${(100 * r.sayi) / max}%"></div></td><td class="sag">${r.sayi}</td></tr>`,
  ).join('');
}

// ---------------------------------------------------------------- uygulama

async function main() {
  const [meta, events, scene, info] = await Promise.all([
    getJSON('meta.json'), getJSON('olaylar.json'), getJSON('web/sahne.json'), getJSON('web/noronlar.json'),
  ]);
  const [kose, yuz, uv, kare, konum, sinif, yaklasik, ofset, noron] = await Promise.all([
    getBin('geo_kose.bin', Float32Array), getBin('geo_yuz.bin', Uint32Array), getBin('geo_uv.bin', Float32Array),
    getBin('kare.bin', Float32Array), getBin('noron_konum.bin', Float32Array), getBin('noron_sinif.bin', Uint8Array),
    getBin('noron_yaklasik.bin', Uint8Array), getBin('spike_ofset.bin', Uint32Array), getBin('spike_noron.bin', Uint32Array),
  ]);
  const spikes = { ofset, noron };
  const T = meta.sure_ms;
  const videos = [$('gozler'), $('ekran')];
  $('gozler').src = KAYIT + 'gozler.mp4';
  $('ekran').src = KAYIT + 'ekran.mp4';

  const decisions = events.filter((e) => e.tur === 'karar');
  const posts = events.filter((e) => e.tur === 'post');
  const placements = events.filter((e) => e.tur === 'yerlestirme');
  const postStart = new Map(posts.map((p) => [p.sira, p.t_ms]));
  $('bilgi').textContent = `fly seed ${meta.sinek_tohumu ?? '?'} · ${sn(T)} · ${posts.length} posts · `
    + `${meta.spike_sayisi.toLocaleString('en-US')} spikes`
    + (meta.bagli ? ' · tethered' : ` · ${placements.length} times put back`);
  $('karar-ozet').textContent = `${decisions.length} decisions`;

  const state = { t: 0, playing: false, speed: 1, selected: null };
  let fly, brain;

  const selectTrace = (title, note, rows, neurons, bodies) => {
    $('iz-baslik').textContent = title;
    $('iz-aciklama').textContent = note;
    traceTable(rows);
    brain.markNeurons(neurons);
    fly.highlight(bodies);
  };

  const pickDecision = (k) => {
    const d = decisions[k];
    state.selected = k;
    const start = postStart.get(d.sira) ?? d.t_ms - d.sure_ms;
    seek(start);
    const ch = d.kanal;
    document.querySelectorAll('#gunluk li').forEach((li, i) => li.classList.toggle('secili', i === k));
    if (!ch) {
      selectTrace('Trace back: lost interest', 'No channel crossed its threshold, so no movement is behind this decision. The fly just scrolled on.', [], [], new Set());
      return;
    }
    const idx = info.kanallar[ch];
    const counts = countSpikes(spikes, idx, Math.floor(start), Math.floor(d.t_ms));
    const rows = [...counts].filter(([, c]) => c > 0).sort((a, b) => b[1] - a[1]).slice(0, 14)
      .map(([n, c]) => ({ ad: `${info.tip[n] || '(untyped)'} <span class="soluk">#${n}</span>`, sayi: c }));
    const active = [...counts].filter(([, c]) => c > 0).length;
    const moved = new Set(Object.values(info.kaslar).filter((m) => m.mn.some((n) => counts.get(n) > 0)).flatMap((m) => m.govde));
    selectTrace(
      `Trace back: ${EYLEM[d.eylem]?.[0] ?? d.eylem}`,
      `${KANAL_ADI[ch] ?? ch} (${idx.length} neurons), from the start of the post to the decision (${sn(d.t_ms - start)}): `
      + `${active} of them fired. ${reason(d.gerekce)}. The glowing body parts are the ones moved by these neurons' muscles.`,
      [{ grup: 'most active (spikes)' }, ...rows], idx, moved,
    );
  };

  const pickBody = (part) => {
    if (!part || !part.kasli) {
      selectTrace('Trace back', part ? `${part.govde.split('/')[1]}: no muscle moves this part directly.` : 'Click a decision or a part of the fly.', [], [], new Set());
      return;
    }
    const a = Math.floor(state.t) - 500, b = Math.floor(state.t);
    const muscles = Object.entries(info.kaslar).filter(([, m]) => m.govde.includes(part.kasli));
    const all = [...new Set(muscles.flatMap(([, m]) => m.mn))];
    const counts = countSpikes(spikes, all, a, b);
    const rows = [];
    for (const [name, m] of muscles) {
      const fired = m.mn.map((n) => [n, counts.get(n)]).filter(([, c]) => c > 0);
      rows.push({ grup: `${kasAdi(name)} (${m.mn.length} MN)` });
      if (!fired.length) rows.push({ ad: '<span class="soluk">no spikes in the last 0.5 s</span>', sayi: 0 });
      for (const [n, c] of fired.sort((x, y) => y[1] - x[1])) rows.push({ ad: `${info.tip[n] || '(untyped)'} <span class="soluk">#${n}</span>`, sayi: c });
    }
    const total = [...counts.values()].reduce((s, c) => s + c, 0);
    selectTrace(
      `Trace back: ${part.kasli}`,
      `${muscles.length} muscles, ${all.length} motor neurons; ${total} spikes between ${sn(a)} and ${sn(b)}. `
      + 'This part moves because of these muscles and the parts it hangs from.',
      rows, all, new Set([part.kasli]),
    );
  };

  fly = new FlyView($('sinek'), scene, { kose, yuz, uv }, kare, $('ekran'), pickBody);
  brain = new BrainView($('beyin'), info, konum, sinif, yaklasik, spikes);
  $('yaklasik').addEventListener('change', (e) => { brain.showApprox = e.target.checked; brain.paintBase(); brain.shown = null; });

  // karar günlüğü
  $('gunluk').innerHTML = decisions.map((d) => {
    const [ad, renk] = EYLEM[d.eylem] ?? [d.eylem, '--ilgi'];
    return `<li><span class="t">${(d.t_ms / 1000).toFixed(1)}</span><span class="n">#${d.sira}</span>`
      + `<span><i class="nokta" style="background:var(${renk})"></i>${ad}</span><span class="d">${d.sure_ms / 1000} s</span></li>`;
  }).join('');
  document.querySelectorAll('#gunluk li').forEach((li, k) => li.addEventListener('click', () => pickDecision(k)));

  // zaman çizgisi işaretleri
  const marks = $('isaretler');
  const drawMarks = () => {
    const w = marks.clientWidth, h = marks.clientHeight;
    marks.width = w * devicePixelRatio;
    marks.height = h * devicePixelRatio;
    const g = marks.getContext('2d');
    g.scale(devicePixelRatio, devicePixelRatio);
    for (const d of decisions) {
      g.fillStyle = css((EYLEM[d.eylem] ?? [0, '--ilgi'])[1]);
      g.fillRect((d.t_ms / T) * w - 1, 2, 2, h - 4);
    }
    g.fillStyle = '#ffffff';
    for (const p of placements) g.fillRect((p.t_ms / T) * w - 1, 0, 2, h);
  };
  new ResizeObserver(drawMarks).observe(marks);

  const slider = $('kaydirac');
  slider.max = T;
  slider.addEventListener('input', () => seek(+slider.value));

  const frameMs = meta.kare_araligi_ms, fps = meta.kare_hizi;
  const videoTime = (t) => Math.max(0, t / frameMs - 1) / fps;
  function syncVideos(force) {
    for (const v of videos) {
      if (v.readyState < 1) continue;
      const target = Math.min(videoTime(state.t), v.duration || Infinity);
      if (state.playing) {
        v.playbackRate = Math.max(0.0625, state.speed * (1000 / frameMs) / fps);
        if (v.paused) v.play().catch(() => {});
        if (Math.abs(v.currentTime - target) > 0.25) v.currentTime = target;
      } else {
        if (!v.paused) v.pause();
        if (force || Math.abs(v.currentTime - target) > 0.02) v.currentTime = target;
      }
    }
  }

  function seek(t) {
    state.t = Math.max(0, Math.min(T, t));
    syncVideos(true);
  }

  const play = (on) => {
    state.playing = on && state.t < T;
    $('oynat').textContent = state.playing ? '❚❚' : '▶';
    syncVideos(true);
  };
  $('oynat').addEventListener('click', () => play(!state.playing));
  $('hiz').addEventListener('change', (e) => { state.speed = +e.target.value; syncVideos(true); });
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' && e.target.type !== 'range') return;
    if (e.code === 'Space') { e.preventDefault(); play(!state.playing); }
    if (e.code === 'ArrowRight') seek(state.t + (e.shiftKey ? 1000 : frameMs));
    if (e.code === 'ArrowLeft') seek(state.t - (e.shiftKey ? 1000 : frameMs));
  });

  let last = performance.now();
  let lastUi = -1;
  function frame(now) {
    const dt = Math.min(100, now - last);
    last = now;
    if (state.playing) {
      state.t += dt * state.speed;
      if (state.t >= T) { state.t = T; play(false); }
      syncVideos(false);
    }
    const held = fly.setTime(state.t);
    brain.setTime(state.t);
    fly.render();
    brain.render();
    if (Math.floor(state.t / 50) !== lastUi) {
      lastUi = Math.floor(state.t / 50);
      slider.value = state.t;
      $('zaman').textContent = sn(state.t);
      $('rozet-tutma').hidden = !held;
      updateNow();
    }
    requestAnimationFrame(frame);
  }

  function updateNow() {
    const past = decisions.filter((d) => d.t_ms <= state.t);
    const post = posts.filter((p) => p.t_ms <= state.t).at(-1);
    const d = past.at(-1);
    const looking = post && (!d || d.sira !== post.sira);
    const lines = [];
    if (post) lines.push(`<div class="soluk">post ${post.sira}: “${post.aciklama}”</div>`);
    if (looking) {
      lines.push(`<div class="eylem">looking… <span class="soluk">${sn(state.t - post.t_ms)}</span></div>`);
    } else if (d) {
      const [ad, renk] = EYLEM[d.eylem] ?? [d.eylem, '--ilgi'];
      lines.push(`<div class="eylem"><i class="nokta" style="background:var(${renk})"></i>${ad}</div><div class="gerekce">${reason(d.gerekce)}</div>`);
    }
    $('simdi').innerHTML = lines.join('');
    document.querySelectorAll('#gunluk li').forEach((li, i) => li.classList.toggle('gelecek', decisions[i].t_ms > state.t));
  }

  videos.forEach((v) => v.addEventListener('loadedmetadata', () => syncVideos(true)));
  requestAnimationFrame(frame);
}

main().catch((err) => {
  $('bilgi').textContent = `error: ${err.message}`;
  console.error(err);
});
