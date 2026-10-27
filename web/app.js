const apiBase = window.MAP_DEMO_API_URL;
const key = "PmIF6Ez34ROeDo7jJGuD";
const styles = {
  "dark-transit": style("dataviz-dark", "#fff", "#000"),
  "modern-light": style("bright-v2", "#000", "#fff"),
  "city-lights": style("streets-v2-dark", "#000", "#ffd900"),
  "ocean-tan": style("basic-v2", "#000", "#fff"),
  eco: style("outdoor-v2", "#A7BEB5", "#044E33"),
  "blue-print": style("winter-v2", "#D2DAE4", "#5D778E"),
  "ruby-routes": style("streets-v2", "#FFFFFF", "#9C111F"),
};

function style(mapId, background, foreground) {
  return {
    url: `https://api.maptiler.com/maps/${mapId}/{z}/{x}/{y}.png?key=${key}`,
    text: {
      fontFamily: {primary: "Semplicita", secondary: "Semplicita", coordinate: "Semplicita"},
      size: {primary: "24", secondary: "12", coordinate: "8"},
      size_demo: {primary: "8", secondary: "4", coordinate: "2"},
      color: {background, primary: foreground, secondary: foreground, coordinate: foreground},
      color_transparent: {background: "#0000", primary: foreground, secondary: foreground, coordinate: foreground},
      textBlock: {padding: "8px", rounded: "8px", spacing: "1"},
      text_block_demo: {padding: "1px", rounded: "3px", spacing: "1"},
    },
  };
}

const titleInput = document.querySelector("#title");
const subtitleInput = document.querySelector("#subtitle");
const styleInput = document.querySelector("#map-style");
const frame = document.querySelector("#poster-frame");
const copy = document.querySelector(".poster-copy");
const previewTitle = document.querySelector("#preview-title");
const previewSubtitle = document.querySelector("#preview-subtitle");
const statusEl = document.querySelector("#job-status");
const downloadEl = document.querySelector("#download");
const generateButton = document.querySelector("#generate");
let orientation = "portrait";
let tileLayer;

const map = L.map("map", {zoomControl: true, attributionControl: true, scrollWheelZoom: true})
  .setView([30.2672, -97.7431], 10);

function replaceTiles() {
  if (tileLayer) map.removeLayer(tileLayer);
  tileLayer = L.tileLayer(styles[styleInput.value].url, {
    tileSize: 64,
    zoomOffset: 2,
    minZoom: 4,
    maxZoom: 13,
    attribution: "&copy; OpenStreetMap contributors · MapTiler",
  }).addTo(map);
  const colors = styles[styleInput.value].text.color;
  copy.style.background = colors.background;
  previewTitle.style.color = colors.primary;
  previewSubtitle.style.color = colors.coordinate;
}
replaceTiles();

function dms(value, positive, negative) {
  const absolute = Math.abs(value);
  const degrees = Math.floor(absolute);
  const minutesFloat = (absolute - degrees) * 60;
  const minutes = Math.floor(minutesFloat);
  const seconds = Math.round((minutesFloat - minutes) * 6000) / 100;
  return `${value >= 0 ? positive : negative} ${degrees}°${minutes}'${seconds}"`;
}

function coordinates() {
  const center = map.getCenter();
  return `${dms(center.lat, "N", "S")} ${dms(center.lng, "E", "W")}`;
}

function sizeTextOverlay() {
  const referenceWidth = orientation === "portrait" ? 552 : 828;
  const scale = frame.clientWidth / referenceWidth;
  copy.style.padding = `${8 * scale}px`;
  copy.style.borderRadius = `${8 * scale}px`;
  copy.style.bottom = `${23 * scale}px`;
  previewTitle.style.fontSize = `${24 * scale}px`;
  previewSubtitle.style.fontSize = `${8 * scale}px`;
}

function updatePreview({updateCoordinates = false} = {}) {
  if (updateCoordinates) subtitleInput.value = coordinates();
  previewTitle.textContent = titleInput.value || "CUSTOM MAP";
  previewSubtitle.textContent = subtitleInput.value;
  document.querySelector("#zoom-readout").textContent = `ZOOM ${map.getZoom()} · ENGINE ${map.getZoom() + 2}`;
  sizeTextOverlay();
}

map.on("moveend zoomend", () => updatePreview({updateCoordinates: true}));
titleInput.addEventListener("input", () => updatePreview());
subtitleInput.addEventListener("input", () => updatePreview());
styleInput.addEventListener("change", () => { replaceTiles(); updatePreview(); });
new ResizeObserver(sizeTextOverlay).observe(frame);

document.querySelectorAll("[data-format]").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll("[data-format]").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  orientation = button.dataset.format;
  frame.className = `poster-frame ${orientation}`;
  setTimeout(() => { map.invalidateSize(); updatePreview({updateCoordinates: true}); }, 180);
}));

document.querySelector("#search").addEventListener("click", async () => {
  const query = document.querySelector("#place").value.trim();
  if (!query) return;
  statusEl.textContent = "Finding that place…";
  try {
    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(query)}`, {headers: {"Accept-Language": "en"}});
    const results = await response.json();
    if (!results.length) throw new Error("Place not found.");
    map.setView([Number(results[0].lat), Number(results[0].lon)], 10);
    titleInput.value = query.split(",")[0].trim();
    updatePreview({updateCoordinates: true});
    statusEl.textContent = "Place found. Pan and zoom to frame the exact print area.";
  } catch (error) {
    statusEl.textContent = error.message || "Could not find that place.";
  }
});

function payload() {
  const bounds = map.getBounds();
  const center = map.getCenter();
  const dimensions = orientation === "portrait"
    ? {map_width: 24, map_height: 36, map_pixel_multiplier: 23}
    : {map_width: 36, map_height: 24, map_pixel_multiplier: 23};
  const bbox = JSON.stringify({
    _southWest: {lat: bounds.getSouth(), lng: bounds.getWest()},
    _northEast: {lat: bounds.getNorth(), lng: bounds.getEast()},
  });
  return [{
    pinList: [],
    center: [center.lat, center.lng],
    zoom: map.getZoom(),
    orientation,
    textPrimary: titleInput.value.trim(),
    textSecondary: "",
    textCoordinates: subtitleInput.value.trim(),
    styling: "basic",
    size: "_24_36",
    tileLayer: styleInput.value,
    bbox,
    tileZoomOffset: 2,
    quantity: 1,
    description: `Map of ${titleInput.value.trim()}`,
    id: crypto.randomUUID(),
    name: "Personalized Map",
    bgImgCode: "",
    isTransparentTextBlock: false,
    text_styling_specs: {id: styleInput.value, iconImg: "", url: styles[styleInput.value].url, text: styles[styleInput.value].text},
    mapDimensionsIn: dimensions,
  }];
}

async function poll(jobId) {
  for (let attempt = 0; attempt < 150; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    const response = await fetch(`${apiBase}/jobs/${jobId}`, {cache: "no-store"});
    const job = await response.json();
    if (job.status === "complete") return job;
    if (job.status === "failed") throw new Error(job.error || "The Tile Engine could not create this map.");
    statusEl.textContent = job.status === "rendering"
      ? "The original Tile Engine is downloading @2x tiles, cropping the bounds, and rendering the 300-DPI PNG…"
      : "A one-off Fargate render task is starting…";
  }
  throw new Error("The map is still rendering. The job can be checked again shortly.");
}

generateButton.addEventListener("click", async () => {
  if (!apiBase) { statusEl.textContent = "The backend is not configured."; return; }
  generateButton.disabled = true;
  downloadEl.hidden = true;
  statusEl.textContent = "Sending the native LyfeCapture payload to the Tile Engine…";
  try {
    const response = await fetch(`${apiBase}/jobs`, {
      method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(payload()),
    });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || "Could not start the map job.");
    const completed = await poll(job.jobId);
    downloadEl.href = completed.downloadUrl;
    downloadEl.download = "lyfe-captures-map.png";
    downloadEl.hidden = false;
    statusEl.textContent = `Native ${completed.width} × ${completed.height} PNG ready. The signed download expires in 15 minutes.`;
  } catch (error) {
    statusEl.textContent = error.message || "Map generation failed.";
  } finally {
    generateButton.disabled = false;
  }
});

updatePreview({updateCoordinates: true});
