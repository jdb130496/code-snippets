// ==UserScript==
// @name         Pluto TV - Hide Floating Player
// @namespace    http://tampermonkey.net/
// @version      5.0
// @description  Hides the persistent docked mini player (bottom-right)
// @match        https://*.pluto.tv/*
// @grant        none
// @run-at       document-start
// ==/UserScript==

(function () {
    'use strict';

    const css = `
        /* ── Exact confirmed selector (hash suffix may change on deploys) ── */
        [class*="PersistentAlwaysOnPlayer_dockPlayer"],

        /* The always-on host wrapper */
        [data-always-on-player-host="true"],

        /* Backup: the inner clipped player */
        [class*="StyledPlayerContainer_clip"],

        /* Belt-and-suspenders: anything with mini-mode that isn't the main player */
        .aa-player-skin.mini-mode {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }
    `;

    function injectStyle() {
        const el = document.getElementById('pluto-hide-docked');
        if (el) return;
        const style = document.createElement('style');
        style.id = 'pluto-hide-docked';
        style.textContent = css;
        (document.head || document.documentElement).appendChild(style);
    }

    injectStyle();

    // Re-inject if React tears out the head
    new MutationObserver(injectStyle)
        .observe(document.documentElement, { childList: true, subtree: true });

})();
