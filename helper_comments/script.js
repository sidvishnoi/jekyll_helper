function get_comments(url, key) {
    document.getElementById('comments').innerHTML = '<div class="load-bar active"><div class="bar"></div><div class="bar"></div><div class="bar"></div></div>';
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
            show_comments(xhr.responseText);
        }
    }
    xhr.open('GET', url + "?mode=get&key=" + key, true);
    xhr.send(null);
}

function show_comments(data) {
    data = JSON.parse(data)["pending"];
    var converter = new showdown.Converter();
    if (data.length == 0) {
    	document.write("no comments to moderate.")
    	return;
    }
    var html = "<div class='comments'>"
    for (var i = 0; i < data.length; ++i) {
        var d = data[i];
        var user = {
            "name": decodeURIComponent(d.author),
            "email": decodeURIComponent(d.email),
            "image": decodeURIComponent(d.image)
        }
        var comment_date = new Date(decodeURIComponent(d.timestamp))
        var timeago = Math.round(((new Date()) - comment_date) * 1.15741e-8) // days
        var comment_content = converter.makeHtml(decodeURIComponent(d.content))
        html += "<div class='comment' id='comment_'" + (i+2) + "'><table>"
        html += "<tr><td><a class='large' href='" + decodeURIComponent(d.url) + "'>" + decodeURIComponent(d.title) + "</a></td><td class='small gray' colspan='2'><abbr title='" + comment_date + "'>" + timeago + " days ago</abbr></td></tr>"
        html += "<tr><td><div class='comment_content'>" + comment_content + "</div></td>"
        html += "<td>" + user.name + "<br/><a class='small' href='mailto:" + user.email + "'>" + user.email + "</a><td><td>" + "<img class='profile' src='" + user.image + "'/></td></tr>"
		html += '<tr><td colspan="3"><input class="tgl tgl-skewed" id="cb'+(i+2)+'" type="checkbox" checked="true" />'
		html += '<label class="tgl-btn" data-tg-off="Delete" data-tg-on="Approve" for="cb'+(i+2)+'"></label></td></tr>'
        html += "</table></div>"
    }
    html += "<button id='comments_submit' onclick='submit(); return false;' class='submit'><span>Submit</span></button>"
    html += "</div>"
    document.getElementById('comments').innerHTML = html;
    var pres = document.getElementsByTagName('pre');
    for (var i = 0; i < pres.length; i++) {
        if (pres[i].firstChild && pres[i].firstChild.nodeName == 'CODE')
            hljs.highlightBlock(pres[i].firstChild);
    }
}


function submit() {
	var cbs = document.querySelectorAll('input[type="checkbox"]');
	var sbt = document.getElementById('comments_submit');
	sbt.classList.add("disable");
	sbt.innerHTML = "<span> submitting . . .</span>";
	var data = {
		"allow": [],
		"delete": []
	}
	for (cb of cbs){
		if (cb.checked == true) {
			data.allow.push(cb.id.substr(2));
		}else{
			data.delete.push(cb.id.substr(2));
		}
	}
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == XMLHttpRequest.DONE) {
            var res = xhr.responseText;
            console.log(res)
            if (res === "moderated."){
            	document.write("moderated. Please add comments to your posts using<br/><pre><code>$ python helper.py --comments publish</code></pre>")
            }else{
            	console.error("error in moderation")
            }
        }
    }
    xhr.open('GET', api_url + "?mode=moderate&key=" + key + "&approved=" + data.allow.join() + "&deleted=" + data.delete.join(), true);
    xhr.send(null);
}




var api_url = "" // "https://script.google.com/macros/s/AKfycbw0...vSF-wXItOd_Z_h7/exec"
var key = "" // "123456789"
get_comments(api_url, key)
