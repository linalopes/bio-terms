function extractAllGoogleAlertsData() {
  var spreadsheetId = 'YOUR_SPREADSHEET_ID'; // Spreadsheet ID
  var sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName('Sheet0'); // Target sheet
  var searchTerms = ['biodesign', 'bioart', 'biohacking', '3D bioprinting']; // Search terms
  var labelName = "Google Alerts - terms"; // Gmail label name
  var label = GmailApp.getUserLabelByName(labelName);

  // Create Gmail label if it doesn't exist
  if (!label) {
      label = GmailApp.createLabel(labelName);
  }

  // Loop through each search term
  searchTerms.forEach(function (searchTerm) {
      var query = `subject:"Alerta do Google - ${searchTerm}" label:inbox`; // Gmail search query
      var threads = GmailApp.search(query);
      Logger.log(`Found ${threads.length} threads for search term: ${searchTerm}`); // Log threads found

      threads.forEach(function (thread) {
          thread.getMessages().forEach(function (message) {
              var date = message.getDate();
              var body = message.getBody(); // HTML-formatted email body
              Logger.log(`Processing email received on: ${date}, body length: ${body.length}`);

              // Regex to extract title, description, and link
              var newsPattern = /<span[^>]*>(.*?)<\/span>[\s\S]*?<div[^>]*color:#252525[^>]*>(.*?)<\/div>/g;
              var matches;
              var newsData = [];

              while ((matches = newsPattern.exec(body)) !== null) {
                  var title = matches[1].replace(/<[^>]*>/g, "").trim(); // Extract title
                  var description = matches[2].replace(/<[^>]*>/g, "").trim(); // Extract description

                  // Extract the link related to this title and description
                  var linkMatch = body.substring(matches.index).match(/<a href="https?:\/\/[^\s"]+?url=([^&"]+)/);
                  if (linkMatch) {
                      var realUrl = decodeURIComponent(linkMatch[1]); // Decode the real URL
                      var source = extractHostname(realUrl); // Extract hostname
                      Logger.log(`Title: ${title}, Description: ${description}, Link: ${realUrl}, Source: ${source}`);
                      // Reordered the data to match the desired column order
                      newsData.push([searchTerm, realUrl, Utilities.formatDate(date, Session.getScriptTimeZone(), "yyyy-MM-dd"), source, title, description]);
                  } else {
                      Logger.log(`No valid link found for title: ${title}`);
                  }
              }

              Logger.log(`Found ${newsData.length} news items in the email.`);

              // Append all extracted data to the spreadsheet
              if (newsData.length > 0) {
                  newsData.forEach(function (row) {
                      sheet.appendRow(row); // Add each row to the sheet
                  });
              } else {
                  Logger.log("No valid news links found in this email.");
              }
          });

          // Apply Gmail label and archive thread
          thread.addLabel(label);
          thread.moveToArchive();
      });
  });
}

// Helper function to extract hostname from a URL
function extractHostname(url) {
  var hostname;
  if (url.indexOf("//") > -1) {
      hostname = url.split('/')[2]; // Remove protocol
  } else {
      hostname = url.split('/')[0];
  }
  hostname = hostname.split(':')[0]; // Remove port
  hostname = hostname.split('?')[0]; // Remove query parameters
  return hostname.replace("www.", ""); // Remove "www."
}
