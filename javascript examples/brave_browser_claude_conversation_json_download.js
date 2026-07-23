const req = indexedDB.open('keyval-store');
req.onsuccess = () => {
  const db = req.result;
  const tx = db.transaction('keyval', 'readonly');
  const store = tx.objectStore('keyval');
  const getReq = store.get('react-query-cache');
  getReq.onsuccess = async () => {
    const cache = getReq.result;
    const match = cache.clientState.queries.find(q =>
      JSON.stringify(q.queryKey).includes('ffad5f0e-b202-4ef2-b1bb-6641a8263aff')
    );
    if (match) {
      const jsonStr = JSON.stringify(match.state.data, null, 2);
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: 'conversation_ab2954d5.json',
          types: [{
            description: 'JSON file',
            accept: { 'application/json': ['.json'] }
          }]
        });
        const writable = await handle.createWritable();
        await writable.write(jsonStr);
        await writable.close();
        console.log('Saved!');
      } catch (err) {
        console.log('Save cancelled or failed:', err);
      }
    } else {
      console.log('Not found in cache.');
    }
  };
};
