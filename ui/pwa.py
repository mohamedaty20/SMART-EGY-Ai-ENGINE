"""
ui/pwa.py — Progressive Web App meta tags + service worker registration.
Call inject_pwa() at the top of every page so the browser can offer
"Add to Home Screen" (iOS) / "Install app" (Android).
"""
from nicegui import ui
from ui.pwa import inject_pwa


def inject_pwa():
    ui.add_head_html("""
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#0b0b0b">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Defects">
<link rel="apple-touch-icon" href="/icon-192.png">
<link rel="apple-touch-icon" sizes="512x512" href="/icon-512.png">

<!-- iOS splash screens (dark, matching the app bg).
     These run while the app is booting, before the first render. -->
<link rel="apple-touch-startup-image"
      href="/splash-1170x2532.png"
      media="(device-width: 390px) and (device-height: 844px) and (-webkit-device-pixel-ratio: 3)">
<link rel="apple-touch-startup-image"
      href="/splash-1179x2556.png"
      media="(device-width: 393px) and (device-height: 852px) and (-webkit-device-pixel-ratio: 3)">
<link rel="apple-touch-startup-image"
      href="/splash-1284x2778.png"
      media="(device-width: 428px) and (device-height: 926px) and (-webkit-device-pixel-ratio: 3)">
<link rel="apple-touch-startup-image"
      href="/splash-1290x2796.png"
      media="(device-width: 430px) and (device-height: 932px) and (-webkit-device-pixel-ratio: 3)">
<link rel="apple-touch-startup-image"
      href="/splash-750x1334.png"
      media="(device-width: 375px) and (device-height: 667px) and (-webkit-device-pixel-ratio: 2)">

<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/service-worker.js")
      .catch(function (err) { console.log("SW reg failed", err); });
  });
}
</script>
""")
