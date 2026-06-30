// ==UserScript==
// @name         Google AI Mode Auto-Expand
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Auto-expand all query previews in Google AI Mode
// @match        https://www.google.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    console.log('AI Mode Auto-Expand: Script loaded');

    function expandAll() {
        let count = 0;
        document.querySelectorAll('div[role="button"][aria-label="Expand query preview"]').forEach(btn => {
            if (btn.getAttribute('aria-expanded') === 'false') {
                btn.click();
                count++;
            }
        });
        if (count > 0) {
            console.log(`AI Mode Auto-Expand: Clicked ${count} expand buttons`);
        }
    }

    setTimeout(() => {
        console.log('AI Mode Auto-Expand: First attempt (2s)');
        expandAll();
    }, 2000);

    setTimeout(() => {
        console.log('AI Mode Auto-Expand: Second attempt (5s)');
        expandAll();
    }, 5000);

    setTimeout(() => {
        console.log('AI Mode Auto-Expand: Third attempt (10s)');
        expandAll();

        setInterval(expandAll, 3000);

        const observer = new MutationObserver(expandAll);
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        console.log('AI Mode Auto-Expand: Continuous monitoring started');
    }, 10000);
})();
