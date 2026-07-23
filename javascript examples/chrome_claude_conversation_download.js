const CONV_UUID = '5feffdb2-f415-42e1-a455-e818b0854df9'; // or a5be4080... whichever is open

const req = indexedDB.open('keyval-store');
req.onsuccess = () => {
  const db = req.result;
  const tx = db.transaction('keyval', 'readonly');
  const store = tx.objectStore('keyval');
  const getReq = store.get('react-query-cache');
  getReq.onsuccess = async () => {
    const cache = getReq.result;
    const match = cache.clientState.queries.find(q =>
      JSON.stringify(q.queryKey).includes(CONV_UUID)
    );
    if (!match) { console.log('Not found'); return; }

    const jsonStr = JSON.stringify(match.state.data, null, 2);
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: `conversation_${CONV_UUID}.json`,
        types: [{ description: 'JSON file', accept: { 'application/json': ['.json'] } }]
      });
      const writable = await handle.createWritable();
      await writable.write(jsonStr);
      await writable.close();
      console.log('Saved!');
    } catch (err) {
      console.log('Save cancelled or failed:', err);
    }
  };
};
