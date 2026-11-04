(function () {
  var script = document.currentScript;
  var url = script.getAttribute("data-url");
  var interval = Number(script.getAttribute("data-interval")) || 8000;

  function text(id, value) {
    var node = document.getElementById(id);
    if (node) {
      node.textContent = value;
    }
  }

  function formatBytes(value) {
    var size = Number(value) || 0;
    var units = ["B", "KB", "MB", "GB", "TB"];
    var index = 0;
    while (size >= 1024 && index < units.length - 1) {
      size /= 1024;
      index += 1;
    }
    var shown = index === 0 ? String(Math.round(size)) : size.toFixed(1);
    return shown + " " + units[index];
  }

  function render(data) {
    var error = document.getElementById("unreachable");
    var grid = document.getElementById("metrics");
    var body = document.getElementById("ports-body");
    if (!data || data.error) {
      if (error) error.hidden = false;
      if (grid) grid.hidden = true;
      if (body) {
        body.replaceChildren();
        var empty = document.createElement("tr");
        var cell = document.createElement("td");
        cell.colSpan = 3;
        cell.textContent = "No listening ports";
        empty.appendChild(cell);
        body.appendChild(empty);
      }
      return;
    }
    if (error) error.hidden = true;
    if (grid) grid.hidden = false;
    text("cpu", data.cpu_percent + "%");
    text("memory", data.memory_percent + "%");
    text(
      "memory-detail",
      formatBytes(data.memory_used_bytes) + " / " + formatBytes(data.memory_total_bytes)
    );
    text("net-in", formatBytes(data.network_in_bytes));
    text("net-out", formatBytes(data.network_out_bytes));
    if (!body) return;
    body.replaceChildren();
    var ports = data.listening_ports || [];
    if (!ports.length) {
      var row = document.createElement("tr");
      var blank = document.createElement("td");
      blank.colSpan = 3;
      blank.textContent = "No listening ports";
      row.appendChild(blank);
      body.appendChild(row);
      return;
    }
    ports.forEach(function (port) {
      var row = document.createElement("tr");
      [port.port, port.protocol, port.address].forEach(function (value) {
        var cell = document.createElement("td");
        cell.textContent = value == null ? "" : String(value);
        row.appendChild(cell);
      });
      body.appendChild(row);
    });
  }

  function tick() {
    fetch(url, {headers: {Accept: "application/json"}})
      .then(function (response) {
        if (!response.ok) return {error: "Host unreachable"};
        return response.json();
      })
      .then(render)
      .catch(function () {
        render({error: "Host unreachable"});
      });
  }

  tick();
  setInterval(tick, interval);
})();
