#!/usr/bin/env python3
from flask import Flask, request, redirect, url_for, render_template_string, jsonify
import os, subprocess, json

BASE_DIR = os.path.dirname(__file__)
PREV_CONN_PATH = os.path.join(BASE_DIR, "previous_connections.json")
CONFIG_PATH = os.path.join(BASE_DIR, "web_config.json")

app = Flask(__name__)

# Helpers
def load_previous():
    try:
        with open(PREV_CONN_PATH) as fp:
            return json.load(fp)
    except Exception:
        return {"previous_addresses": {}}

def save_previous(data):
    with open(PREV_CONN_PATH, "w") as fp:
        json.dump(data, fp, indent=2)

def load_config():
    try:
        with open(CONFIG_PATH) as fp:
            return json.load(fp)
    except Exception:
        default = {"title": "RPI BT Manager", "autoplay": False}
        with open(CONFIG_PATH, "w") as fp:
            json.dump(default, fp, indent=2)
        return default

def run_bt_cmd(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        return {"rc": r.returncode, "out": r.stdout, "err": r.stderr}
    except Exception as e:
        return {"rc": 99, "out": "", "err": str(e)}

# Routes
INDEX_HTML = """
<!doctype html>
<title>{{cfg.title}}</title>
<h2>{{cfg.title}}</h2>

<h3>Add / Update device</h3>
<form method="post" action="/add">
 Name: <input name="name" size=30 placeholder="Device name">
 MAC: <input name="mac" size=30 placeholder="AA:BB:CC:DD:EE:FF">
 <button type="submit">Add / Update</button>
</form>

<h3>Available devices (lazy load)</h3>
<button id="refreshDevices" onclick="fetchDevices()">Refresh devices</button>
<span id="devicesStatus"></span>
<table id="availTable" border=1 cellpadding=4 style="margin-top:8px;">
<tr><th>Name</th><th>MAC</th><th>Actions</th></tr>
<!-- populated by JS -->
</table>

<p>Current devices saved:</p>
<table border=1 cellpadding=4>
<tr><th>Order</th><th>Name</th><th>MAC</th><th>Count</th><th>Actions</th></tr>
{% for k, d in devices %}
<tr>
 <td>{{k}}</td>
 <td>{{d.name}}</td>
 <td>{{d.mac_addr}}</td>
 <td>{{d.connection_count}}</td>
 <td>
  <form style="display:inline" method="post" action="/pair">
    <input type="hidden" name="mac" value="{{d.mac_addr}}">
    <button type="submit">Pair</button>
  </form>
  <form style="display:inline" method="post" action="/connect">
    <input type="hidden" name="mac" value="{{d.mac_addr}}">
    <button type="submit">Connect</button>
  </form>
  <form style="display:inline" method="post" action="/disconnect">
    <input type="hidden" name="mac" value="{{d.mac_addr}}">
    <button type="submit">Disconnect</button>
  </form>
  <form style="display:inline" method="post" action="/unpair" onsubmit="return confirm('Unpair and remove from list?');">
    <input type="hidden" name="mac" value="{{d.mac_addr}}">
    <button type="submit">Unpair</button>
  </form>
 </td>
</tr>
{% endfor %}
</table>

<h3>Reorder (comma-separated MACs, top-to-bottom)</h3>
<form method="post" action="/reorder">
  <input name="order" size=80 value="{{ordered_macs}}">
  <button type="submit">Save order</button>
</form>

<h3>Settings</h3>
<form method="post" action="/settings">
 Title: <input name="title" value="{{cfg.title}}">
 Autoplay on connect: <input type="checkbox" name="autoplay" {% if cfg.autoplay %}checked{% endif %}>
 <button type="submit">Save</button>
</form>
<p><i>Note: Commands run bluetoothctl; this server must run on the Pi and have permission to control bluetooth.</i></p>

<script>
function setStatus(msg){ document.getElementById('devicesStatus').innerText = msg; }
function postForm(path, params){
  const body = new URLSearchParams(params);
  return fetch(path, {method:'POST', body, headers:{'Content-Type':'application/x-www-form-urlencoded'}})
    .then(()=>location.reload());
}
function fetchDevices(){
  setStatus('Loading...');
  const table = document.getElementById('availTable');
  // clear rows except header
  while(table.rows.length>1) table.deleteRow(1);
  fetch('/devices').then(r => r.json()).then(data=>{
    if(!Array.isArray(data)) { setStatus('No devices'); return; }
    data.forEach(d=>{
      const row = table.insertRow();
      const nameCell = row.insertCell();
      const macCell = row.insertCell();
      const actionCell = row.insertCell();
      nameCell.innerText = d.name || '';
      macCell.innerText = d.mac || '';
      // Add button
      const addBtn = document.createElement('button');
      addBtn.innerText = 'Add';
      addBtn.onclick = ()=> {
        postForm('/add', {name: d.name || d.mac, mac: d.mac});
      };
      actionCell.appendChild(addBtn);
      // Pair button
      const pairBtn = document.createElement('button');
      pairBtn.innerText = 'Pair';
      pairBtn.style.marginLeft='6px';
      pairBtn.onclick = ()=> {
        postForm('/pair', {mac: d.mac});
      };
      actionCell.appendChild(pairBtn);
      // Connect button (optional)
      const connBtn = document.createElement('button');
      connBtn.innerText = 'Connect';
      connBtn.style.marginLeft='6px';
      connBtn.onclick = ()=> {
        postForm('/connect', {mac: d.mac});
      };
      actionCell.appendChild(connBtn);
    });
    setStatus('Found ' + data.length + ' device(s)');
  }).catch(err=>{
    setStatus('Error: ' + (err.message || err));
  });
}
// optionally auto-load when opening the page (lazy): uncomment next line
// window.addEventListener('load', fetchDevices);
</script>
"""

@app.route("/", methods=["GET"])
def index():
    conns = load_previous()
    devices = sorted(conns.get("previous_addresses", {}).items(), key=lambda x: int(x[0]))
    ordered_macs = ",".join([d.get("mac_addr","") for k,d in devices])
    cfg = load_config()
    return render_template_string(INDEX_HTML, devices=devices, ordered_macs=ordered_macs, cfg=cfg)

@app.route("/connect", methods=["POST"])
def connect():
    mac = request.form.get("mac")
    # trust the device before connecting so it persists as trusted
    run_bt_cmd(f"bluetoothctl trust {mac}")
    res = run_bt_cmd(f"bluetoothctl connect {mac}")
    # autoplay if configured
    cfg = load_config()
    if cfg.get("autoplay"):
        try:
            clean = mac.replace(":", "_")
            subprocess.call(f"qdbus --system org.bluez /org/bluez/hci0/dev_{clean}/player0 org.bluez.MediaPlayer1.Play", shell=True)
        except Exception:
            pass
    return redirect(url_for("index"))

@app.route("/pair", methods=["POST"])
def pair():
    mac = request.form.get("mac")
    # perform pairing
    run_bt_cmd(f"bluetoothctl pair {mac}")
    return redirect(url_for("index"))

@app.route("/disconnect", methods=["POST"])
def disconnect():
    mac = request.form.get("mac")
    res = run_bt_cmd(f"bluetoothctl disconnect {mac}")
    return redirect(url_for("index"))

@app.route("/unpair", methods=["POST"])
def unpair():
    mac = request.form.get("mac")
    # run bluetooth remove first
    run_bt_cmd(f"bluetoothctl remove {mac}")
    # remove from JSON if present
    conns = load_previous()
    items = conns.get("previous_addresses", {})
    keys_to_remove = [k for k,v in items.items() if v.get("mac_addr") == mac]
    for k in keys_to_remove:
        items.pop(k, None)
    # reindex keys to simple 1..N
    new_items = {}
    for idx, (_, v) in enumerate(sorted(items.items(), key=lambda x: int(x[0])), start=1):
        new_items[str(idx)] = v
    conns["previous_addresses"] = new_items
    save_previous(conns)
    return redirect(url_for("index"))

@app.route("/reorder", methods=["POST"])
def reorder():
    order = request.form.get("order", "")
    macs = [m.strip() for m in order.split(",") if m.strip()]
    conns = load_previous()
    items = conns.get("previous_addresses", {})
    # build a map mac->entry
    map_mac = {v.get("mac_addr"): v for v in items.values()}
    new_items = {}
    idx = 1
    # add in the order provided
    for mac in macs:
        if mac in map_mac:
            new_items[str(idx)] = map_mac.pop(mac)
            idx += 1
    # append any remaining devices
    for v in map_mac.values():
        new_items[str(idx)] = v
        idx += 1
    conns["previous_addresses"] = new_items
    save_previous(conns)
    return redirect(url_for("index"))

@app.route("/settings", methods=["POST"])
def settings():
    cfg = load_config()
    title = request.form.get("title")
    # checkbox only present when checked
    cfg["autoplay"] = True if request.form.get("autoplay") else False
    if title:
        cfg["title"] = title
    with open(CONFIG_PATH, "w") as fp:
        json.dump(cfg, fp, indent=2)
    return redirect(url_for("index"))

@app.route("/add", methods=["POST"])
def add():
    name = (request.form.get("name") or "").strip()
    mac = (request.form.get("mac") or "").strip()
    if not mac:
        return redirect(url_for("index"))
    conns = load_previous()
    items = conns.get("previous_addresses", {})
    # try update if mac exists
    for k, v in items.items():
        if v.get("mac_addr") == mac:
            if name:
                v["name"] = name
            conns["previous_addresses"] = items
            save_previous(conns)
            return redirect(url_for("index"))
    # else add new entry at next index
    try:
        next_idx = max([int(k) for k in items.keys()]) + 1 if items else 1
    except Exception:
        next_idx = 1
    items[str(next_idx)] = {"name": name or mac, "mac_addr": mac, "connection_count": 0}
    conns["previous_addresses"] = items
    save_previous(conns)
    return redirect(url_for("index"))

@app.route("/devices", methods=["GET"])
def devices():
    """
    Return JSON list of discovered devices from bluetoothctl.
    Format: [{ "mac": "...", "name": "..." }, ...]
    """
    try:
        # run bluetoothctl devices (fast enough and non-blocking with timeout)
        r = subprocess.run("bluetoothctl devices", shell=True, capture_output=True, text=True, timeout=10)
        out = r.stdout.strip()
    except Exception as e:
        return jsonify([])

    devices = []
    for line in out.splitlines():
        # expected: "Device AA:BB:CC:DD:EE:FF Name Here"
        line = line.strip()
        if not line.startswith("Device "):
            continue
        parts = line.split(' ', 2)
        # parts[1] = MAC, parts[2] = Name (if present)
        mac = parts[1] if len(parts) > 1 else ''
        name = parts[2] if len(parts) > 2 else ''
        devices.append({"mac": mac, "name": name})
    return jsonify(devices)

if __name__ == "__main__":
    # Run on all interfaces so you can access from other devices.
    app.run(host="0.0.0.0", port=8080, debug=False)
