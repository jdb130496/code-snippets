function markAllAsNotImportant() {
  const query = 'is:important';
  let threads = GmailApp.search(query, 0, 100);
  
  while (threads.length > 0) {
    GmailApp.markThreadsNotImportant(threads);
    threads = GmailApp.search(query, 0, 100);
  }
}

