// Phase 2 status page: confirms the local backend, database and Python
// environment are reachable. Not the application UI (that is Phase 8).
(function () {
  "use strict";

  var API = "/api/v1";

  function getJson(path) {
    return fetch(API + path, { headers: { Accept: "application/json" } }).then(function (response) {
      return response.json().then(function (body) {
        return { ok: response.ok, status: response.status, body: body };
      });
    });
  }

  function setBadge(key, level, text) {
    var badge = document.querySelector('[data-key="' + key + '"] .badge');
    badge.className = "badge " + level;
    badge.textContent = text;
  }

  function renderDetails(info, env, db) {
    var list = document.getElementById("details");
    list.replaceChildren();
    var rows = [
      ["Version", info.version],
      ["Environment", info.environment],
      ["Listening on", info.host + ":" + info.port + (info.local_only ? " (this computer only)" : "")],
      ["Python", info.python_version + " on " + info.platform],
      ["SQLite", db.sqlite_version ? db.sqlite_version + ", journal " + db.journal_mode : "unavailable"],
      ["Playwright", env.playwright.version ? env.playwright.version : "not installed"],
      [
        "Playwright Chromium",
        env.playwright.chromium_installed ? "installed" : "not installed (optional in Phase 2)",
      ],
    ];
    rows.forEach(function (pair) {
      var row = document.createElement("div");
      var dt = document.createElement("dt");
      var dd = document.createElement("dd");
      dt.textContent = pair[0];
      dd.textContent = pair[1];
      row.append(dt, dd);
      list.append(row);
    });
  }

  function check() {
    var message = document.getElementById("message");
    ["backend", "database", "python"].forEach(function (key) {
      setBadge(key, "pending", "Checking");
    });
    message.textContent = "Contacting the local backend\u2026";

    Promise.all([
      getJson("/health"),
      getJson("/health/database"),
      getJson("/health/environment"),
      getJson("/system/info"),
    ])
      .then(function (results) {
        var health = results[0], db = results[1], env = results[2], info = results[3];

        setBadge("backend", health.ok ? "ok" : "error", health.ok ? "ONLINE" : "ERROR");
        setBadge("database", db.ok ? "ok" : "error", db.ok ? "CONNECTED" : "ERROR");

        var envStatus = env.body.status;
        setBadge(
          "python",
          envStatus === "ok" ? "ok" : envStatus === "degraded" ? "warn" : "error",
          envStatus === "error" ? "NOT READY" : envStatus === "degraded" ? "READY (notes)" : "READY"
        );

        renderDetails(info.body, env.body, db.body);

        if (health.ok && db.ok && envStatus !== "error") {
          message.textContent = "Phase 2 development environment is ready.";
        } else {
          var problems = [];
          if (!db.ok) problems.push("Database: " + (db.body.error || "unavailable"));
          if (envStatus === "error") problems.push(env.body.notes.join(" "));
          message.textContent = "Attention needed. " + problems.join(" ");
        }
      })
      .catch(function () {
        setBadge("backend", "error", "OFFLINE");
        setBadge("database", "error", "UNKNOWN");
        setBadge("python", "error", "UNKNOWN");
        message.textContent =
          "The local backend did not respond. Start it with scripts\\start.ps1 and reload this page.";
      });
  }

  document.getElementById("recheck").addEventListener("click", check);
  check();
})();
