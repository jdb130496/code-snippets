const fs = require('fs');
const path = require('path');
const { PDFDocument } = require('D:/Programs/nodejs/node_modules/pdf-lib');

async function stitch() {
    const inputDir = 'D:/dev/pdf-images/cut';
    const outputFile = 'D:/dev/pdf-images/stitched.pdf';

    const pdfDoc = await PDFDocument.create();

    // Get all page_XXXX.png files in order
    const files = fs.readdirSync(inputDir)
        .filter(f => f.match(/^page_\d+\.png$/))
        .sort()
        .map(f => path.join(inputDir, f));

    console.log(`Found ${files.length} images...`);

    for (const file of files) {
        const imgBytes = fs.readFileSync(file);
        const img = await pdfDoc.embedPng(imgBytes);
        const page = pdfDoc.addPage([img.width, img.height]);
        page.drawImage(img, { x: 0, y: 0, width: img.width, height: img.height });
        console.log(`Added: ${path.basename(file)}`);
    }

    const pdfBytes = await pdfDoc.save();
    fs.writeFileSync(outputFile, pdfBytes);
    console.log(`Done! → ${outputFile}`);
}

stitch().catch(console.error);
