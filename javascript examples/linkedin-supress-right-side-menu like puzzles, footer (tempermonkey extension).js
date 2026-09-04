// ==UserScript==
// @name         LinkedIn Cleaner
// @namespace    http://tampermonkey.net/
// @version      2.4
// @description  Hides messaging popup, Today's Puzzles, LinkedIn News, and sidebar footer
// @match        *://www.linkedin.com/*
// @grant        none
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

function injectCSS() {
    if (document.getElementById('li-hide-elements')) return;
    const style = document.createElement('style');
    style.id = 'li-hide-elements';
    style.textContent = `
        /* Messaging popup */
        .msg-overlay-bubble-header,
        .msg-overlay-bubble-header__details,
        .msg-overlay-list-bubble,
        .msg-overlay-conversation-bubble,
        [class*="msg-overlay-list-bubble"],
        #msg-overlay-list-bubble-header__button {
            display: none !important;
            visibility: hidden !important;
        }
        /* Today's Puzzles */
        #feedRightNavGamesComponentRef {
            display: none !important;
        }
        /* LinkedIn News */
        [componentkey="c8924d5c-8ea5-48a1-8557-49237a1fb9d4"] {
            display: none !important;
        }
        /* Classic footer */
        .global-footer-compact {
            display: none !important;
        }
    `;
    (document.head || document.documentElement).appendChild(style);
}
    function hideSidebarFooter() {
        // Hide footer containing About link
        document.querySelectorAll('a[href="https://about.linkedin.com/"]').forEach(link => {
            const footer = link.closest('footer');
            if (footer) {
                footer.style.setProperty('display', 'none', 'important');
            }
        });

        // Hide copyright div via stable SVG id
        document.querySelectorAll('svg#linkedin-logo-xxsmall').forEach(svg => {
            const div = svg.parentElement;
            if (div) {
                div.style.setProperty('display', 'none', 'important');
            }
        });

        // Classic footer fallback
        document.querySelectorAll('.global-footer-compact').forEach(el => {
            el.style.setProperty('display', 'none', 'important');
        });
    }

    function hideElements() {
        // Messaging
        [
            '.msg-overlay-bubble-header',
            '.msg-overlay-bubble-header__details',
            '.msg-overlay-list-bubble',
            '.msg-overlay-conversation-bubble',
            '#msg-overlay-list-bubble-header__button',
        ].forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                let root = el;
                while (root.parentElement &&
                       root.parentElement.classList.toString().includes('msg-overlay')) {
                    root = root.parentElement;
                }
                root.style.setProperty('display', 'none', 'important');
            });
        });

        // Today's Puzzles
        const puzzles = document.getElementById('feedRightNavGamesComponentRef');
        if (puzzles) puzzles.style.setProperty('display', 'none', 'important');

        // LinkedIn News (componentkey + text fallback)
        document.querySelectorAll('[componentkey="c8924d5c-8ea5-48a1-8557-49237a1fb9d4"]')
            .forEach(el => el.style.setProperty('display', 'none', 'important'));
        document.querySelectorAll('p').forEach(el => {
            if (el.textContent.trim() === 'LinkedIn News') {
                let root = el;
                for (let i = 0; i < 5; i++) {
                    if (!root.parentElement) break;
                    root = root.parentElement;
                }
                root.style.setProperty('display', 'none', 'important');
            }
        });

        // Sidebar footer
        hideSidebarFooter();
    }

    injectCSS();

    // More attempts at longer intervals to catch late-loading footer
    [500, 2000, 4000, 6000, 8000, 12000].forEach(delay => {
        setTimeout(() => { injectCSS(); hideElements(); }, delay);
    });

    setTimeout(() => {
        let debounceTimer;
        const observer = new MutationObserver(() => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                injectCSS();
                hideElements();
            }, 150);
        });
        if (document.body) {
            observer.observe(document.body, { childList: true, subtree: true });
        }
    }, 3000);

})();
