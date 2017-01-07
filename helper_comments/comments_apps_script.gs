var settings = {
	"deleteKey": "123456789",
	// keep this key safe, same as the key in comments.py
	"checkProfanity": true,
	// if set to true, this will use a public API to check to profanity in comment body.
	// Set true only if comments are not very long in length and do not include a lot of code and freespaces,
	// otherwise it generally finds profanity even if there is no profanity
}

function doGet(e) {
	return handleResponse(e);
}

function doPost(e) {
	return handleResponse(e);
}

function disallow_user(user) {
	// check user in <user_blacklist> sheet, tested based of user (email)
	var blacklist = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("user_blacklist").getRange("a:a").getValues().toString()
	if (blacklist.indexOf(user) > -1) {
		return true; // block user
	} else {
		return false; // allow
	}
}

function disallow_content(content) {
	/* XSS regex check */
	var markdown_is_bad = function(s) {
	// currently doesn't allow inline amrkdown code also - TODO
		s = decodeURIComponent(s)
		s = s.split(/```/);
		var is_broken = false;
		if (s.length % 2 == 0) {
			is_broken = true;
			return true
		}

		if (!is_broken) {
			var in_markdown = false;
			for (var i in s) {
				in_markdown = i % 2 == 1;
				if (!in_markdown) {
					s[i] = s[i].match(/<[a-z\/][^>]*>/g);
					if (s[i] != null) return true
				}
			}
		}
		return false;
	}

	/* Profanity check via api */
	var has_profanity = function(s){
		var api_response = false;
		content = s.replace('/(?:\r\n|\r|\n)/g', '').split("\n").join();
		var l = s.length;
		var chunksize = 500;
		if (l > chunksize) {
			// break text in smaller parts - needed in URLFetchApp and in API (supports only get request)
			for (var i = 0; i < l; i += chunksize) {
				var chunk = s.substring(i, i + chunksize);
				var intermediate_response = UrlFetchApp.fetch("http://www.purgomalum.com/service/containsprofanity?text=" + encodeURIComponent(chunk));
				api_response = api_response || (intermediate_response == "true" ? true : false);
				if (api_response == true) {
					return true; // contains profanity
				}
			}
		} else {
			api_response = UrlFetchApp.fetch("http://www.purgomalum.com/service/containsprofanity?text=" + encodeURIComponent(s));
			if (api_response == "true") {
				return true;
			}
		}
	}

	/* check in <words_blacklist> */
	var has_blacklist_words = function(s){
		var profanity_sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("words_blacklist");
		var blacklisted_words = profanity_sheet.getRange("a:a" + profanity_sheet.getLastRow()).getValues().toString().split(",");
		var l = blacklisted_words.length;
		for (var i = 0; i < l; i++) {
			if (blacklisted_words[i] !== "" && s.toLowerCase().indexOf(blacklisted_words[i].toLowerCase()) > -1) {
				return true; // contains a blacklisted word
			}
		}
	}

	var ct = decodeURIComponent(content)
	if (markdown_is_bad(ct)) return true;
	if (settings["checkProfanity"]) {
		if (has_profanity(ct)) return true;
	}
	if (has_blacklist_words(ct)) return true;

	/* else allow content */
	return false;
}

function addComment(e) {
	// add a comment to <pending>
	var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("pending");
	try {
		var name = e.parameter.name;
		var email = e.parameter.email;
		var ct = e.parameter.ct;
		var parent = e.parameter.p;
		var slug = e.parameter.slug;
		var url = e.parameter.url;
		var image = e.parameter.image;
		var formattedDate = Utilities.formatDate(new Date(), "GMT", "yyyy-MM-dd'T'HH:mm:ss'Z'");
		if (disallow_user(email)) return "you are not allowed"; // user not allowed
		if (disallow_content(ct)) return "content not allowed"; // block based on content
		sheet.appendRow([formattedDate, slug, url, parent, name, image, email, ct]);
		return "successfully added";
	} catch (e) {
		return e;
	}
}

function getjson() {
	// returns the <pending> comments JSON
	var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("pending");
	var rows = sheet.getDataRange();
	var numRows = rows.getNumRows();
	var numCols = rows.getNumColumns();
	var values = rows.getValues();

	var tt = "";
	tt += '{\n\t"pending" : [\n';
	var header = values[0];
	for (var i = 1; i < numRows; ++i) {
		tt += '\t{\n';
		var row = values[i];
		for (var j = 0; j < numCols; ++j) {
			tt += ' \t "' + header[j] + '" : "' + encodeURIComponent(row[j]) + ((j == numCols - 1) ? '"\n' : '", \n');
		}
		tt += (i == numRows - 1) ? '\t}\n' : '\t},\n';
	}
	tt += '\t]\n}';
	return tt;
}

function movePending(approve, disallow) {
	// moves content of <pending> to <waiting> and deletes (moves to <deleted>) [disallow] comments
	var approved = approve.split(",")
	var disallowed = disallow.split(",")
	var sheet_pending = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("pending");
	var sheet_waiting = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("waiting");
	var sheet_deleted = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("deleted");

	var rows = sheet_pending.getDataRange();
	var numCols = rows.getNumColumns();


	for (var i = disallowed.length - 1; i >= 0; i--) {
      try {
        sheet_deleted.getRange(sheet_deleted.getLastRow() + 1, 1, 1, numCols).setValues(sheet_pending.getRange(parseInt(disallowed[i]), 1, 1, numCols).getValues()); // moves to <deleted>
		sheet_pending.deleteRow(disallowed[i]); //  deletes from <pending>
      }catch(e){
        // do nothing
      }
	}
	sheet_waiting.getRange(sheet_waiting.getLastRow() + 1, 1, approved.length, numCols).setValues(sheet_pending.getRange(2, 1, approved.length, numCols).getValues());
	sheet_pending.deleteRows(2, approved.length);
}

function moveWaiting(len) {
	// moves content of <waiting> to <published>
	var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("waiting");
	var rows = sheet.getDataRange();
	var numCols = rows.getNumColumns();
	var range = sheet.getRange(2, 1, len, numCols).getValues();
	var sheet2 = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("published");
	sheet2.getRange(sheet2.getLastRow() + 1, 1, len, numCols).setValues(range);
	sheet.deleteRows(2, len);
}

function handleResponse(e) {
	// this prevents concurrent access overwritting data
	// [1] https://gsuite-developers.googleblog.com/2011/10/concurrency-and-google-apps-script.html
	// we want a public lock, one that locks for all invocations
	var lock = LockService.getPublicLock();
	lock.waitLock(30000); // wait 30 seconds before conceding defeat.

	try {
		var mode = e.parameter.mode;

		if (mode === "post") {
			return ContentService.createTextOutput(addComment(e));
		} else if (mode === "get") {
			return ContentService.createTextOutput(getjson());
		} else if (mode === "moderate") {
			if (e.parameter.key === settings["deleteKey"]) {
				movePending(e.parameter.approved, e.parameter.deleted)
				return ContentService.createTextOutput("moderated.")
			} else {
				return ContentService.createTextOutput("moderation failed. invalid key.")
			}
		} else if (mode === "publish") {
			if (e.parameter.key === settings["deleteKey"]) {
				moveWaiting(e.parameter.num);
				return ContentService.createTextOutput("comments published");
			} else {
				return ContentService.createTextOutput("comments not published. bad key.");
			}
		} else {
			return ContentService.createTextOutput("idk something happened");
		}
	} catch (e) {
		// if error return this
		return ContentService.createTextOutput(e);
	} finally { //release lock
		lock.releaseLock();
	}
}
