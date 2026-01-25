// Hide BOTTOM toolbar (Home/Track/Shop)
const toolbarLabel = document.querySelector('.wd-toolbar-label');
if (toolbarLabel) {
  let parent = toolbarLabel.parentElement;
  while (parent && parent !== document.body) {
    parent = parent.parentElement;
    const labelsInParent = parent.querySelectorAll('.wd-toolbar-label').length;
    if (labelsInParent >= 2) {
      parent.style.display = 'none';
      console.log('✓ Bottom toolbar hidden!');
      break;
    }
  }
}

// Hide TOP toolbar (Header with Wishlist/Cart/Logo)
const topElements = [
  '.whb-column',
  '.wd-header-wishlist',
  '.wd-header-cart',
  '.whb-header',
  'header',
  '[class*="whb-"]'
];

topElements.forEach(selector => {
  document.querySelectorAll(selector).forEach(el => {
    // Check if it's part of the header (contains wishlist or cart)
    if (el.querySelector('.wd-header-wishlist, .wd-header-cart, img[alt*="logo"]')) {
      el.style.display = 'none';
    }
  });
});

// Also hide header by finding logo parent
const logo = document.querySelector('img[alt*="astro"], img[alt*="logo"]');
if (logo) {
  let parent = logo;
  for (let i = 0; i < 10; i++) {
    parent = parent.parentElement;
    if (parent.tagName === 'HEADER' || parent.classList.contains('header')) {
      parent.style.display = 'none';
      console.log('✓ Top header hidden!');
      break;
    }
  }
}

// Hide WhatsApp floating button
const whatsappIcons = document.querySelectorAll('.fa-whatsapp, .fa-brands.fa-whatsapp, i.fa-whatsapp');
whatsappIcons.forEach(icon => {
  // Hide the icon itself
  icon.style.display = 'none';
  
  // Hide all parent containers up to 10 levels
  let parent = icon.parentElement;
  for (let i = 0; i < 10; i++) {
    if (parent && parent !== document.body) {
      parent.style.display = 'none';
      parent = parent.parentElement;
    }
  }
});

// Also hide any floating/fixed elements at bottom right
document.querySelectorAll('*').forEach(el => {
  const computedStyle = window.getComputedStyle(el);
  if (computedStyle.position === 'fixed' || computedStyle.position === 'sticky') {
    // Check if it contains whatsapp icon
    if (el.querySelector('.fa-whatsapp') || el.innerHTML.includes('whatsapp')) {
      el.style.display = 'none';
    }
  }
});

console.log('✓ All toolbars and floating buttons hidden!');
alert('✓ Top/Bottom toolbars and WhatsApp button are now hidden!');

// Add CSS to keep them hidden during print
const style = document.createElement('style');
style.textContent = `
  /* Hide bottom toolbar */
  .wd-toolbar, .wd-toolbar-label, 
  [class*="wd-toolbar"],
  
  /* Hide top header */
  .whb-column, .wd-header-wishlist, 
  .wd-header-cart, .wd-header-divider,
  .whb-header, header,
  [class*="whb-"],
  img[alt*="logo"], img[alt*="astro"],
  
  /* Hide WhatsApp and floating buttons */
  .fa-whatsapp, 
  .fa-brands.fa-whatsapp,
  i.fa-whatsapp,
  [class*="whatsapp"],
  a[href*="whatsapp"],
  a[href*="wa.me"],
  [style*="position: fixed"],
  [style*="position:fixed"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
  }
  
  @media print {
    .wd-toolbar, .wd-toolbar-label, 
    [class*="wd-toolbar"],
    .whb-column, .wd-header-wishlist, 
    .wd-header-cart, header,
    [class*="whb-"],
    .fa-whatsapp, [class*="whatsapp"] {
      display: none !important;
    }
  }
  
  /* Remove top padding/margin after hiding header */
  body, main, .content {
    padding-top: 0 !important;
    margin-top: 0 !important;
  }
`;
document.head.appendChild(style);
