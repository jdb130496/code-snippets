function downloadCSVFromGmail() {
  // Define constants for subject and folder names.
  const SUBJECT = "files for research";
  const FOLDER_NAME = "Downloaded CSVs";

  Logger.log("--- Starting CSV Download Script Debug (Stage 1: Download SharePoint Excel Files) ---");
  Logger.log(`Configured Subject to search: "${SUBJECT}"`);
  Logger.log(`Configured Google Drive Folder: "${FOLDER_NAME}"`);

  let folder;
  try {
    const folders = DriveApp.getFoldersByName(FOLDER_NAME);
    if (folders.hasNext()) {
      folder = folders.next();
      Logger.log(`Drive Folder Status: Found existing folder "${folder.getName()}" (ID: ${folder.getId()})`);
    } else {
      folder = DriveApp.createFolder(FOLDER_NAME);
      Logger.log(`Drive Folder Status: Created new folder "${folder.getName()}" (ID: ${folder.getId()})`);
    }
  } catch (e) {
    Logger.log(`ERROR: Could not access or create Google Drive folder. Error: ${e.message}`);
    return;
  }

  const searchQuery = `subject:"${SUBJECT}"`;
  Logger.log(`Gmail Search Query being used: "${searchQuery}"`);

  let threads = [];
  try {
    threads = GmailApp.search(searchQuery);
    Logger.log(`Gmail Search Result: Found ${threads.length} email threads.`);
  } catch (e) {
    Logger.log(`ERROR: Could not perform Gmail search. Error: ${e.message}`);
    return;
  }

  if (threads.length === 0) {
    Logger.log(`CRITICAL: No emails found matching the subject: "${SUBJECT}". Double-check subject EXACTNESS.`);
    Logger.log("--- Script Finished (No emails found) ---");
    return;
  }

  let filesDownloadedCount = 0;

  threads.forEach((thread, threadIndex) => {
    Logger.log(`Processing Thread #${threadIndex + 1} (Subject: "${thread.getFirstMessageSubject()}", ID: ${thread.getId()})`);
    const messages = thread.getMessages();
    Logger.log(`  Found ${messages.length} messages in this thread.`);

    messages.forEach((message, messageIndex) => {
      Logger.log(`    Processing Message #${messageIndex + 1} (From: ${message.getFrom()}, Date: ${message.getDate()})`);
      Logger.log(`      Message ID: ${message.getId()}`);
      Logger.log(`      Message is a Draft: ${message.isDraft()}`);
      Logger.log(`      Message is Unread: ${message.isUnread()}`);

      // Attempt with standard getAttachments() first.
      const attachments = message.getAttachments();
      Logger.log(`      Result from message.getAttachments(): Found ${attachments.length} attachments.`);

      if (attachments.length === 0) {
        Logger.log("        No standard attachments found. Attempting to extract and download from SharePoint URLs in message body...");
        try {
          const downloadedFromUrls = extractAndDownloadFromSharePointUrls(message, folder);
          filesDownloadedCount += downloadedFromUrls;
          if (downloadedFromUrls === 0) {
            Logger.log("        No files found by extracting and downloading from SharePoint URLs either.");
            Logger.log("        This confirms the files are likely embedded inline (dragged into email body) and/or structured unusually, or SharePoint access failed.");
            Logger.log("        Final RECOMMENDATION: Please ask the sender to attach CSV files using the standard paperclip icon in Gmail.");
          }
        } catch (e) {
          Logger.log(`        ERROR: Could not extract/download from URLs. Error: ${e.message}`);
        }
      } else {
        Logger.log("        Processing standard attachments...");
        attachments.forEach((file, fileIndex) => {
          const fileName = file.getName();
          const fileType = file.getContentType();
          Logger.log(`          Attachment #${fileIndex + 1}: Name: "${fileName}", Type: "${fileType}"`);
          if (fileType === "text/csv" || fileName.toLowerCase().endsWith(".csv")) {
            try {
              folder.createFile(file);
              Logger.log(`            SUCCESS: Saved "${fileName}" to Google Drive.`);
              filesDownloadedCount++;
            } catch (e) {
              Logger.log(`            ERROR: Failed to save "${fileName}". Error: ${e.message}`);
            }
          } else {
            Logger.log(`            SKIPPING: Attachment "${fileName}" is not a CSV (Type: ${fileType}).`);
          }
        });
      }
    });
  });

  if (filesDownloadedCount === 0) {
    Logger.log("--- Script Finished: No files were successfully downloaded. ---");
  } else {
    Logger.log(`--- CSV Download Script Complete: Successfully downloaded ${filesDownloadedCount} files. ---`);
  }
}

/**
 * Extracts SharePoint URLs from the email's HTML body and attempts to download them.
 * @param {GoogleAppsScript.Gmail.GmailMessage} message The Gmail message object.
 * @param {GoogleAppsScript.Drive.Folder} folder The Google Drive folder to save files to.
 * @returns {number} The number of files successfully extracted and saved from URLs.
 */
function extractAndDownloadFromSharePointUrls(message, folder) {
  Logger.log("    Attempting to extract and download from SharePoint URLs...");
  let downloadedCount = 0;

  // Regex to find <a> tags with href pointing to sharepoint.com and capturing the URL and text (filename)
  // This regex specifically looks for the filename immediately after an <img> tag within the <a>.
  const sharepointLinkRegex = /<a[^>]*href="([^"]+\.sharepoint\.com[^"]*)"[^>]*>.*?<img[^>]*>\s*([^<]+?\.csv)<\/a>/gim;

  const htmlBody = message.getBody();
  if (htmlBody) {
    Logger.log("      Checking HTML body for SharePoint URLs...");
    let match;
    while ((match = sharepointLinkRegex.exec(htmlBody)) !== null) {
      const url = match[1];
      const fileName = match[2].trim(); // Get the filename from the link text
      downloadedCount += downloadSharePointFile(url, fileName, folder);
    }
  }

  // Also check plain text body for any direct SharePoint URLs, though less likely to have names
  if (downloadedCount === 0) {
    const plainBody = message.getPlainBody();
    if (plainBody) {
      Logger.log("      Checking plain text body for raw SharePoint URLs (with filenames)...");
      // This regex captures:
      // 1. Optional icon URL in brackets: (?:\[[^\]]+\])?
      // 2. The filename ending in .csv: ([^<\s]+?\.csv)
      // 3. The SharePoint URL in angle brackets: <(https?:\/\/[^\s>]+sharepoint\.com[^>]+)>
      const plainTextSharepointLinkRegex = /(?:\[[^\]]+\])?([^<\s]+?\.csv)<(https?:\/\/[^\s>]+sharepoint\.com[^>]+)>/g;
      let match;
      while ((match = plainTextSharepointLinkRegex.exec(plainBody)) !== null) {
        const fileName = match[1].trim();
        const url = match[2];
        downloadedCount += downloadSharePointFile(url, fileName, folder);
      }
    }
  }
  return downloadedCount;
}

/**
 * Attempts to download a file from a SharePoint URL and save it as an Excel file.
 * This is a staging function to verify initial download success.
 *
 * @param {string} fileUrl The URL of the SharePoint file.
 * @param {string} fileName The desired filename for the downloaded file (e.g., "2000-2005.csv").
 * @param {GoogleAppsScript.Drive.Folder} folder The Google Drive folder to save files to.
 * @returns {number} 1 if successfully downloaded, 0 otherwise.
 */
function downloadSharePointFile(fileUrl, fileName, folder) {
  Logger.log(`        Found potential SharePoint file URL: ${fileUrl}`);
  Logger.log(`        Attempting to download and save as temporary Excel file: "${fileName}"`);

  try {
    const response = UrlFetchApp.fetch(fileUrl, {muteHttpExceptions: true});

    if (response.getResponseCode() === 200) {
      const excelBlob = response.getBlob();
      // Ensure the temporary file is saved as .xlsx
      const tempExcelFileName = fileName.replace(/\.csv$/i, '.xlsx');
      excelBlob.setName(tempExcelFileName);

      const tempFile = folder.createFile(excelBlob);
      Logger.log(`            SUCCESS: Saved temporary Excel file "${tempFile.getName()}" (ID: ${tempFile.getId()}).`);
      return 1; // Success
    } else {
      Logger.log(`            ERROR: Failed to download "${fileName}" from ${fileUrl}. Response Code: ${response.getResponseCode()}, Message: ${response.getContentText().substring(0, 200)}...`);
      if (response.getResponseCode() === 401 || response.getResponseCode() === 403) {
        Logger.log(`            NOTE: A 401/403 error suggests an authentication/permission issue for the SharePoint file.`);
      }
      return 0;
    }
  } catch (e) {
    Logger.log(`            ERROR: Exception during download: ${e.message}`);
    return 0;
  }
  // No finally block to trash files, as the goal is to inspect them in Drive.
}
