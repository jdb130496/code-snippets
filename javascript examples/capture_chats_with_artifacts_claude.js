const sel = "body > div.root > div > div.w-full.relative.min-w-0 > div > div.max-md\\:absolute.top-0.right-0.bottom-0.left-0.z-20.md\\:flex-grow-0.md\\:flex-shrink-0.md\\:basis-0.overflow-hidden.h-full.max-md\\:flex-1 > div > div.flex-1.overflow-hidden.h-full.bg-bg-100 > div > div > div.ease-out.duration-200.relative.flex.w-full.flex-1.overflow-x-auto.overflow-y-scroll > div > div > div";

async function extract() {
    // First, close any open artifact to capture clean chat text
    const closeBtn = document.querySelector('[aria-label="Close artifact"]');
    if (closeBtn) {
        closeBtn.click();
        await new Promise(r => setTimeout(r, 500));
    }
    
    // Get only main artifact buttons (those in the chat messages, not in the artifact panel)
    const allBtns = document.querySelectorAll('.line-clamp-1');
    const mainBtns = Array.from(allBtns).filter(btn => {
        // Exclude buttons that are inside the artifact panel
        return !btn.closest('[class*="ease-out duration-200"]') && 
               !btn.closest('[class*="overflow-x-auto overflow-y-scroll"]');
    });
    
    console.log(`Found ${mainBtns.length} main artifact buttons (filtered from ${allBtns.length} total buttons)`);
    
    // Capture the main chat content WITHOUT any artifact open
    const chatContent = document.querySelector('body > div.root').innerText;
    
    const artifacts = [];
    
    // Now extract all artifacts
    for (let i = 0; i < mainBtns.length; i++) {
        const title = mainBtns[i].textContent.trim();
        
        // Changed: relaxed filter to allow shorter titles (>= 3 chars instead of > 5)
        if (title.length >= 3 && title.length < 200) {
            console.log(`Clicking button [${i + 1}]: "${title}" (${title.length} chars)`);
            
            mainBtns[i].click();
            await new Promise(r => setTimeout(r, 2000));
            
            const panel = document.querySelector(sel);
            if (panel) {
                panel.scrollTop = panel.scrollHeight;
                await new Promise(r => setTimeout(r, 800));
                
                const code = panel.innerText;
                
                artifacts.push({
                    index: i + 1,
                    title: title,
                    code: code
                });
                
                console.log(`✓ Extracted [${i + 1}/${mainBtns.length}]:`, title, '-', code.length, 'chars');
            } else {
                console.log(`✗ Panel not found for button [${i + 1}]: "${title}"`);
            }
        } else {
            console.log(`Skipped button [${i + 1}]: "${title}" (${title.length} chars - outside valid range)`);
        }
    }
    
    // Build output: chat first, then all artifacts with version numbers
    let out = chatContent + '\n\n';
    
    artifacts.forEach((artifact) => {
        out += '\n' + '='.repeat(80) + '\n';
        out += `ARTIFACT #${artifact.index}: ${artifact.title}\n`;
        out += '='.repeat(80) + '\n\n';
        out += artifact.code + '\n\n';
    });
    
    const blob = new Blob([out], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chat-export.txt';
    a.click();
    console.log(`✓ Downloaded ${artifacts.length} artifacts, ${out.length} chars total`);
}

extract();
