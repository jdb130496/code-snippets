// ==UserScript==
// @name         Gemini Auto-Expand
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Automatically expand all collapsed responses in Gemini
// @match        *://gemini.google.com/*
// @grant        none
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';
    console.log('Gemini Auto-Expand: Script loaded');

    function expandAll() {
        let count = 0;

        // Find all expand_more icons and click their parent button
        document.querySelectorAll('mat-icon[data-mat-icon-name="expand_more"]').forEach(icon => {
            const btn = icon.closest('button');
            if (btn) {
                btn.click();
                count++;
            }
        });

        if (count > 0) {
            console.log(`Gemini Auto-Expand: Clicked ${count} expand buttons`);
        }
    }

    setTimeout(() => {
        console.log('Gemini Auto-Expand: First attempt (2s)');
        expandAll();
    }, 2000);

    setTimeout(() => {
        console.log('Gemini Auto-Expand: Second attempt (5s)');
        expandAll();
    }, 5000);

    setTimeout(() => {
        console.log('Gemini Auto-Expand: Third attempt (10s)');
        expandAll();

        // Continuous monitoring for new messages
        setInterval(expandAll, 3000);

        const observer = new MutationObserver(expandAll);
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        console.log('Gemini Auto-Expand: Continuous monitoring started');
    }, 10000);
})();
