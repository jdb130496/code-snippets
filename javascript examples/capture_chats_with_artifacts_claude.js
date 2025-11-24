const sel = "body > div.root > div > div.w-full.relative.min-w-0 > div > div.max-md\\:absolute.top-0.right-0.bottom-0.left-0.z-20.md\\:flex-grow-0.md\\:flex-shrink-0.md\\:basis-0.overflow-hidden.h-full.max-md\\:flex-1 > div > div.flex-1.overflow-hidden.h-full.bg-bg-100 > div > div > div.ease-out.duration-200.relative.flex.w-full.flex-1.overflow-x-auto.overflow-y-scroll > div > div > div";

async function extract() {
    const btns = document.querySelectorAll('.line-clamp-1');
    const artifacts = new Map();
    
    for (let i = 0; i < btns.length; i++) {
        const title = btns[i].textContent.trim();
        if (title.length > 5 && title.length < 200) {
            btns[i].click();
            await new Promise(r => setTimeout(r, 1500));
            
            const panel = document.querySelector(sel);
            if (panel) {
                panel.scrollTop = panel.scrollHeight;
                await new Promise(r => setTimeout(r, 500));
                
                const code = panel.innerText;
                artifacts.set(title, code);
                console.log('Extracted:', title, '-', code.length, 'chars');
            }
        }
    }
    
    let out = document.querySelector('body > div.root').innerText + '\n\n';
    
    artifacts.forEach((code, title) => {
        out += '\n' + '='.repeat(80) + '\n';
        out += 'ARTIFACT: ' + title + '\n';
        out += '='.repeat(80) + '\n\n';
        out += code + '\n\n';
    });
    
    const blob = new Blob([out], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chat-export.txt';
    a.click();
    console.log('✓ Downloaded ' + out.length + ' chars total');
}

extract();
