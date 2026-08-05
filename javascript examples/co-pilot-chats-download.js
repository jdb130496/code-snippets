(function() {
    const container = document.querySelector('.fui-Virtualizer-Scroll-View-Dynamic__container');
    if (!container) { console.log('Container not found!'); return; }
    
    container.scrollTop = 0;
    let fullText = '';
    let currentScroll = 0;
    const step = 200;
    const delay = 800;
    let lastText = '';

    console.log('Starting capture — do not touch the page...');

    setTimeout(() => {
        const timer = setInterval(() => {
            const visibleText = container.innerText.trim();
            
            if (visibleText !== lastText) {
                fullText += visibleText + '\n\n';
                lastText = visibleText;
                console.log(`Position: ${currentScroll} | Captured ${visibleText.length} chars`);
            }

            const maxHeight = container.scrollHeight;
            currentScroll += step;
            container.scrollTop = currentScroll;

            if (currentScroll >= maxHeight) {
                clearInterval(timer);

                let markdown = '# Copilot Chat Export\n\n';
                markdown += `**Exported:** ${new Date().toLocaleString()}\n\n---\n\n`;
                markdown += fullText;

                const blob = new Blob([markdown], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'copilot-chat.md';
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 1000);

                console.log('✅ DONE! Check downloads for copilot-chat.md');
            }
        }, delay);
    }, 1000);
})();
