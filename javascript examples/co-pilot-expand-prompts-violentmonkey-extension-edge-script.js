// ==UserScript==
// @name         Copilot Auto-Expand Show More
// @namespace    Violentmonkey Scripts
// @version      5.0.0
// @description  Automatically clicks "See more" buttons in Microsoft Copilot
// @match        *://copilot.microsoft.com/*
// @match        *://www.bing.com/*
// @match        *://m365.cloud.microsoft/*
// @match        *://*.microsoft.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
    'use strict';

    function expandAll() {
        let count = 0;
        document.querySelectorAll('button[aria-label="See more"][aria-expanded="false"]').forEach(btn => {
            btn.click();
            count++;
        });
        if (count > 0) console.log(`Copilot Expand: Clicked ${count} button(s)`);
    }

    // Retry every second for first 60 seconds after page load
    let attempts = 0;
    const interval = setInterval(() => {
        expandAll();
        attempts++;
        if (attempts >= 60) clearInterval(interval);
    }, 1000);

    // Watch forever for new messages being added
    let debounceTimer;
    const startObserver = () => {
        new MutationObserver(() => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(expandAll, 500);
        }).observe(document.body, { childList: true, subtree: true });
        console.log('Copilot Expand v5: Observer running on', window.location.href);
    };

    if (document.body) {
        startObserver();
    } else {
        document.addEventListener('DOMContentLoaded', startObserver);
    }

})();
