# BC250 Waveshare Decky (staged, not installed)

Read-only plugin for the existing localhost `/status.json` endpoint of
`scripts/waveshare_host_metrics.py --serve`. It never creates another collector,
starts a service, requests root or controls power. Missing/stale data is explicit.

API/build shape verified against SteamDeckHomebrew/decky-plugin-template,
repository revision `90d0780e882a17f5714fc6de044c645f22608290`:
`main.py`, `src/index.tsx`, `plugin.json`, `package.json`, `rollup.config.js` and
`tsconfig.json`. No upstream install/migration code was executed or copied.
Build dependencies are pinned to the inspected template versions. Project code is MIT.

Installation on AMD, live Decky compatibility and a real gaming-session layout
remain unaccepted; copying this directory is not a proof of installation.
