// ==UserScript==
// @name         Google AI Mode Auto-Expand
// @namespace    http://tampermonkey.net/
// @version      1.5
// @description  Auto-expand all query previews in Google AI Mode
// @match        https://www.google.com/*
// @grant        none
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    function expandBtn(btn) {
        if (btn.getAttribute('aria-expanded') === 'false') {
            setTimeout(() => btn.click(), 50);
        }
    }

    function expandAll() {
        document.querySelectorAll('div[role="button"].l1LGWd[aria-expanded="false"]').forEach(expandBtn);
    }

    setTimeout(() => expandAll(), 2000);
    setTimeout(() => expandAll(), 5000);
    setTimeout(() => {
        expandAll();

        // Watch for aria-expanded attribute changes specifically
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(m => {
                if (
                    m.type === 'attributes' &&
                    m.attributeName === 'aria-expanded' &&
                    m.target.getAttribute('aria-expanded') === 'false' &&
                    m.target.matches('div[role="button"].l1LGWd')
                ) {
                    setTimeout(() => m.target.click(), 50);
                }

                // Also handle newly added nodes
                m.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        node.querySelectorAll?.('div[role="button"].l1LGWd[aria-expanded="false"]')
                            .forEach(expandBtn);
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['aria-expanded']
        });

    }, 10000);

})();
