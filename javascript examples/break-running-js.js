let id = setTimeout(() => {}, 0);
while (id--) clearInterval(id);
console.log('All scripts stopped');
