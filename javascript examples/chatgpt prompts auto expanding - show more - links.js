// ==UserScript==
// @name         ChatGPT Auto-Expand Show More
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  Automatically expand all collapsed user messages in ChatGPT
// @match        *://chatgpt.com/*
// @match        *://*.chatgpt.com/*
// @grant        none
// @run-at       document-start
// ==/UserScript==
(function() {
    'use strict';
    console.log('ChatGPT Auto-Expand: Script loaded at document-start');

    function expandAll() {
        let count = 0;
        document.querySelectorAll('[data-testid="collapsible-user-message-toggle"][aria-expanded="false"]').forEach(btn => {
            btn.click();
            count++;
        });
        if (count > 0) {
            console.log(`ChatGPT Auto-Expand: Expanded ${count} message(s)`);
        }
    }

    let debounceTimer = null;
    function debouncedExpand() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(expandAll, 300);
    }

    setTimeout(expandAll, 1500);

    const observer = new MutationObserver(debouncedExpand);
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['aria-expanded'] });

    console.log('ChatGPT Auto-Expand: Monitoring started');
})();
