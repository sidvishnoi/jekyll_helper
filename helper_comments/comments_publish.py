'''
comment helper module for Jekyll
by Sid vishnoi
https://github.com/sidvishnoi
'''

from datetime import datetime
from urllib import unquote
from hashlib import md5
from dateutil.parser import parse
import requests
import yaml


def print_error():
    ''' print a specific error message '''
    msg = '\x1b[1;31;40m' # bold red color
    msg += "Comment with same timestamp already in comments."
    msg += '\x1b[0m' # normal color
    print msg

def new_comment_body(data, ctype, parent, settings):
    ''' return new comment/reply body '''
    return {
        "comment" if ctype == 0 else "reply": None,
        "id": parent,
        "date": data["comment_date"].isoformat(),
        "user": data["comment_author"],
        "email": md5(data["comment_email"]).hexdigest() \
            if settings["saveAsmd5"] else data["comment_email"],
        "image": data["comment_image"],
        "content": data["comment_content"]
    }


def delete_pending(settings, length):
    ''' moves comments from <waiting> sheet to <published>, post processing '''
    if length > 0:
        print "moving comments from waiting to published sheet."
        url = settings["apiUrl"] + \
        "?mode=publish&key=" + settings["deleteKey"] + "&num=" + str(length)
        req = requests.get(url, allow_redirects=True)
        print req.text
    else:
        print "All Done."


def update_comments(settings):
    '''
    saves comments from received json to local files
    '''

    # CHECK AND EDIT SETTINGS
    try:
        conf_file = open('source/_config.yml')
        conf_yaml = yaml.load(conf_file)
        conf_file.close()
    except IOError:
        print '\x1b[1;31;40m' + "Coudn't read _config.yml" + '\x1b[0m'
        return

    try:
        comments_conf = conf_yaml["jekyll-comments"]
    except KeyError:
        print '\x1b[1;31;40m' + "Coudn't read <jekyll-comments> in _config.yml" + '\x1b[0m'
        return

    try:
        settings["commentsDir"] = "_data/comments/" \
        if comments_conf["commentsDir"] == '' \
        else comments_conf["commentsDir"]
        # this is where are comments are saved
        # default: "_data/comments/"
        settings["logFile"] = "comments.log" \
        if comments_conf["logFile"] == '' \
        else comments_conf["logFile"]
        # this file will keep a list of files in which comments are updated,
        # useful in partial builds.
        # default: "jekyll-comments/comments.log"
        settings["apiUrl"] = comments_conf["apiUrl"]
        # [REQUIRED] the url you received from Google Apps Script step, e.g.
        # "apiUrl": "https://script.google.com/macros/s/AKfycb...PMyh4aXQ6c_/exec",
        settings["saveAsmd5"] = False \
        if comments_conf["saveAsmd5"] == '' \
        else comments_conf["saveAsmd5"]
        # if True, the email ids in _data/comments/*.yml are saved as md5 hashes,
        # useful if you make your _data/comments/*.yml public
        # otherwise emails are stored as it is
        # default: False
    except KeyError:
        print '\x1b[1;31;40m' + "Error in getting settings from _config.yml" + '\x1b[0m'
        return

    if settings["apiUrl"] == "":
        print '\x1b[1;31;40m' + "You must set your apiUrl first in settings." + '\x1b[0m'
        return

    settings["deleteKey"] = "123456789" if settings["deleteKey"] == "" else settings["deleteKey"]

    # BEGIN MAIN FUNCTION

    print "requesting comments from : ", settings["apiUrl"]
    req = requests.get(settings["apiUrl"] + "?mode=publish_get", allow_redirects=True)
    comments = req.json()["pending"]

    total_comments = len(comments)
    if total_comments == 0:
        print '\x1b[5;30;43m' + "No comments to add." + '\x1b[0m'
        return
    print '\x1b[5;30;43m' + "adding", total_comments, "comments..." + '\x1b[0m'
    comment_counter = 0

    for comment in comments:

        slug = settings["commentsDir"] + unquote(comment["slug"]).decode('utf8') + ".yaml"
        try:
            comment_file = open(slug, 'r')
        except IOError:
            comment_file = open(slug, 'w')
            yaml.safe_dump({'comments': []}, comment_file, default_flow_style=False, indent=2)
            comment_file.close()
            comment_file = open(slug, 'r')


        old_data = yaml.load(comment_file)
        old_comments = old_data["comments"]

        comment_id = unquote(comment["id"]).decode('utf8')
        comment_content = unquote(comment["content"]).decode('utf8')
        comment_date = parse(unquote(comment["timestamp"]).decode('utf8'))
        comment_date = (comment_date - comment_date.utcoffset()).replace(tzinfo=None) # utc datetime
        comment_author = unquote(comment["author"]).decode('utf8')
        comment_email = unquote(comment["email"]).decode('utf8')
        comment_image = unquote(comment["image"]).decode('utf8')
        comment_url = unquote(comment["url"]).decode('utf8')

        comment_data = {
            "comment_id": comment_id,
            "comment_content": comment_content,
            "comment_date": comment_date,
            "comment_author": comment_author,
            "comment_email": comment_email,
            "comment_image": comment_image,
            "comment_url": comment_url,
            "comment_slug": unquote(comment["slug"]).decode('utf8')
        }


        old_comment_ids = [x["id"] for x in old_comments]
        if comment_id == "c":
            new_comment_id = 1
            if old_comment_ids != []:
                new_comment_id = max([int(x.split("c")[1]) for x in old_comment_ids]) + 1
                # calculated based on highest index in old_comments
            new_comment = new_comment_body(comment_data, 0, "c" + str(new_comment_id), settings)
            oldtimestamps = [x["date"] for x in old_comments]
            # used to skip comments with same timestamp
            if comment_date.isoformat() in oldtimestamps:
                print_error()
            else:
                comment_counter += 1
                old_comments.append(new_comment)
        else:
            parent_comment_id = old_comment_ids.index(comment_id) # find parent comment id
            old_comment = old_comments[parent_comment_id]
            if "replies" in old_comment:
                old_reply_ids = [int(x["id"].split("-")[1]) for x in old_comment["replies"]]
                new_reply_id = max(old_reply_ids) + 1
                new_reply = new_comment_body(comment_data, 1, \
                    comment_id + "-" + str(new_reply_id), settings)
                oldtimestamps = [x["date"] for x in old_comment["replies"]]
                if comment_date.isoformat() in oldtimestamps:
                    print_error()
                else:
                    comment_counter += 1
                    old_comment["replies"].append(new_reply)
            else:
                comment_counter += 1
                old_comment["replies"] = []
                new_reply = new_comment_body(comment_data, 1, comment_id + "-1", settings)
                old_comment["replies"].append(new_reply)

        comment_file.close()
        old_data["updated"] = datetime.now().isoformat()
        old_data["count"] = {
            "comments": len(old_comments),
            "replies": sum([len(x["replies"]) for x in old_comments if "replies" in x])
        }

        comment_file = open(slug, 'w')
        yaml.safe_dump(old_data, comment_file, default_flow_style=False, indent=2)
        comment_file.close()

    print "added", comment_counter, "comments."
    delete_pending(settings, comment_counter)


def main():
    '''
    main function caller
    '''
    settings = {
        "deleteKey": "",
        # a key that is known only to you - this is the same key as in comments.gs file
        # allows: comment deletion, get comments, user blacklisting
        # keep it safe, don't add comments.gs and comments.py to your git repo
        # default: "123456789"
    }

    update_comments(settings)

if __name__ == '__main__':
    main()
