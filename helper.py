'''
Jekyll Helper by Sid Vishnoi
https://github.com/sidvishnoi/jekyll_helper/
'''
import os
import argparse
import readline
from datetime import datetime, timedelta
import subprocess
from dateutil.tz import tzlocal
import yaml

class AutoComplete(object):
    '''
    Python get_text autocomplete from a list
    hints from : http://stackoverflow.com/questions/5637124/tab-completion-in-pythons-raw-inpu
    '''
    def createlist_completer(self, options):
        '''
        This is a closure that creates a method that autocompletes from
        the given list.
        Since the autocomplete function can't be given a list to complete from
        a closure is used to create the list_completer function with a list to complete
        from.
        '''
        def list_completer(text, state):
            '''
            suggest from a list (options) based on text
            '''
            line = readline.get_line_buffer()
            if not line:
                return [c for c in options][state]
            else:
                return [c for c in options if line in c][state]
        self.list_completer = list_completer

class Color(object):
    '''
    colored print in terminal
    http://stackoverflow.com/a/287944
    '''
    header = '\033[95m'
    blue = '\033[94m'
    green = '\033[92m'
    yellow = '\033[93m'
    error = '\033[91m'
    normal = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'

def local_server(directory):
    '''
    shows a given directory on a localhost port
    '''
    import threading
    os.chdir(directory)
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler # Python 3
    except ImportError:
        from BaseHTTPServer import HTTPServer # Python 2
        from SimpleHTTPServer import SimpleHTTPRequestHandler as BaseHTTPRequestHandler

    server = HTTPServer(('localhost', 8000), BaseHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.deamon = True
    def server_up():
        ''' initialize a local server'''
        thread.start()
        print Color.blue + 'local server available at http://127.0.0.1:' + str(server.server_port)\
         + Color.normal
    def server_down():
        ''' kill the initialized local server'''
        raw_input(Color.header + "Press [Enter] to kill server:\n" + Color.normal)
        server.shutdown()
        print 'stopping server on port {}'.format(server.server_port)

    server_up()
    server_down()

def deploy(mthds, methods):
    '''
    deploy "mthds" using methods defined in "methods"
    '''
    for mthd in mthds:
        print Color.header + "Deploying via " + Color.bold + Color.yellow + mthd + Color.normal\
         + Color.header + " method" + Color.normal
        os.system(methods[mthd])

def clear_temp():
    ''' clear .tmp folder '''
    os.system("mkdir -p .tmp")
    os.system("rm -rf .tmp/*")

def clear_public():
    ''' clear the public folder '''
    os.system("rm -rf public/*")

def create_assets(verbose):
    '''
    builds static files in source/assets/ directory
    '''
    clear_temp()
    print Color.blue + "building static assets" + Color.normal
    os.system("cp -rf source/assets/ source/_config.yml source/Gemfile source/Gemfile.lock .tmp/")
    conf_file = open(".tmp/_config.yml", 'r')
    conf_yaml = yaml.load(conf_file)
    conf_file.close()
    try:
        conf_yaml['exclude'].remove("assets")
    except KeyError:
        conf_yaml['exclude'] = []

    try:
        del conf_yaml['paginate']
    except KeyError:
        pass

    try:
        del conf_yaml['paginate_path']
    except KeyError:
        pass

    try:
        conf_yaml['gems'].remove("jekyll-paginate")
    except KeyError:
        pass

    conf_yaml['exclude'].append("_posts")


    conf_file = open(".tmp/_config.yml", 'w')
    yaml.safe_dump(conf_yaml, conf_file, default_flow_style=False, indent=2)
    conf_file.close()

    os.chdir(".tmp")
    os.system("bundle exec jekyll build" + ("" if verbose else " --quiet"))

    os.chdir("..")

    os.system("rsync -a .tmp/_site/assets public/")

def create_category(section, verbose):
    '''
    builds a category under public/ folder
    if you put a comma (,) (without space) at end of a directory, it will also build its subdir,
        but excludes its "pages" and index.html
    '''
    if len(section) == 0:
        categories = [f for f in os.listdir("content/") \
        if os.path.isdir(os.path.join("content", f)) \
        and f.find("pages") < 0]
        for cat in categories:
            if cat != "pages":
                categories.extend([cat + "/" + f for f in os.listdir("content/" + cat + "/") \
                    if os.path.isdir(os.path.join("content/" + cat + "/", f)) \
                    and f.find("pages") < 0])

        auto = AutoComplete()
        auto.createlist_completer(categories)
        readline.set_completer_delims('\t')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(auto.list_completer)

        categories = sorted(categories)

        print Color.header + "Select the categories you want to build. Leave empty to continue." +\
        Color.normal
        if verbose:
            print Color.blue +"Categories: " + Color.normal, categories

        while True:
            sec = raw_input(Color.bold + Color.blue + "Category: " + Color.normal)
            if sec.replace(",", "") in categories:
                section.append(sec)
            elif sec != "":
                print Color.error + "category not found" + Color.normal
            if sec == "":
                break

    if len(section) == 0:
        return

    section = [s.replace("content/", "") for s in section]
    for cat in section:
        inc_child = True if cat.find(",") > -1 else False
        cat = cat.replace(",", "")
        print Color.blue + "building posts under section:" + cat + \
        (" and its sub directories" if inc_child else "") + Color.normal
        clear_temp()
        os.system("cp -rf source/* .tmp/")
        os.system("cp -rf content/" + cat + "/* " + ".tmp/_posts/")
        os.system("mv .tmp/_posts/pages/* .tmp/")
        if not inc_child:
            os.system("rm -r .tmp/_posts/*/") # delete remaining dir from -posts, exlcude files
        conf_file = open(".tmp/_config.yml", 'r')
        conf_yaml = yaml.load(conf_file)
        conf_file.close()
        try:
            conf_yaml['feed']['path'] = "/" + cat + "/feed.xml"
        except KeyError:
            pass
        try:
            conf_yaml['paginate_path'] = "/" + cat + "/page/:num/"
        except KeyError:
            pass
        conf_file = open(".tmp/_config.yml", 'w')
        yaml.safe_dump(conf_yaml, conf_file, default_flow_style=False, indent=2)
        conf_file.close()
        os.chdir(".tmp")
        os.system("bundle exec jekyll build" + ("" if verbose else " --quiet"))
        os.chdir("..")
        os.system("mv .tmp/_site/index.html .tmp/_site/sitemap.xml" + " "\
         + ".tmp/_site/" + cat + "/")
        os.system("mv .tmp/_site/page" " " + ".tmp/_site/" + cat)
        os.system("rsync -a .tmp/_site/* public/")


def create_home_page(arg, verbose):
    '''
    creates home page
    more features coming soon using arg (== settings["homepage"])
    '''
    print Color.blue + "building home page" + Color.normal
    clear_temp()
    os.system("cp -rf source/* .tmp/")
    os.system("cp -rf content/* " + ".tmp/_posts/")
    os.system("mv .tmp/_posts/index.html .tmp/")
    os.system("rm .tmp/_posts/pages/*")
    conf_file = open(".tmp/_config.yml", 'r')
    conf_yaml = yaml.load(conf_file)
    conf_file.close()
    try:
        del conf_yaml['paginate_path']
    except KeyError:
        pass
    conf_file = open(".tmp/_config.yml", 'w')
    yaml.safe_dump(conf_yaml, conf_file, default_flow_style=False, indent=2)
    conf_file.close()
    os.chdir(".tmp")
    os.system("bundle exec jekyll build --limit_posts 8" + ("" if verbose else " --quiet"))
    os.chdir("..")
    os.system("mv .tmp/_site/index.html public/")

def create_pages(verbose):
    ''' build static pages '''
    print Color.blue + "building static pages" + Color.normal
    clear_temp()
    os.system("cp -rf source/* .tmp/")
    os.system("cp -rf content/pages/* " + ".tmp/")
    conf_file = open(".tmp/_config.yml", 'r')
    conf_yaml = yaml.load(conf_file)
    conf_file.close()
    try:
        del conf_yaml['paginate_path']
    except KeyError:
        pass
    conf_file = open(".tmp/_config.yml", 'w')
    yaml.safe_dump(conf_yaml, conf_file, default_flow_style=False, indent=2)
    conf_file.close()
    os.chdir(".tmp")
    os.system("bundle exec jekyll build" + ("" if verbose else " --quiet"))
    os.chdir("..")
    os.system("rsync -a .tmp/_site/* public/")

def create_sitemap(siteurl):
    '''
    creates a sitemap.xml file for all URLs in public folder
    '''
    print Color.blue + "building sitemap.xml ..." + Color.normal,
    sitemap_file = open("public/sitemap.xml", "w")
    sitemap_file.write('''<?xml version="1.0" encoding="UTF-8"?>\n\
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n''')
    for path, _, files in os.walk("public/"):
        for filename in files:
            sitemap_file.write(('\t<url>\n\t\t<loc>'\
                + os.path.join(path, filename)\
                .replace('public/', siteurl)\
                .replace('index.html', "")\
                + '</loc>\n\t</url>\n')\
            if '.html' in filename else "")
    sitemap_file.write('</urlset>')
    print Color.green + "done building public/sitemap.xml" + Color.normal
    sitemap_file.close()

def create_post(settings, verbose):
    '''
    create a new post
    - use autocomplete to find available layouts, category directories
    - create a file at desired location, with frontmatter help
    '''
    layout, section, title = "", "", ""

    def get_text(msg):
        ''' override the raw_input() with colored message '''
        return raw_input(Color.bold + Color.blue + msg + Color.normal)

    print Color.header + "Create a new post" + Color.normal + "\n"

    layouts = sorted([f.replace(".html", "") for f in os.listdir("source/_layouts/") \
        if os.path.isfile(os.path.join("source/_layouts/", f))])

    auto = AutoComplete()
    auto.createlist_completer(layouts)
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(auto.list_completer)

    if verbose:
        print Color.header + "Layouts:" + Color.normal, layouts

    while True:
        layout = get_text("Layout: ")
        if layout in layouts:
            break
        else:
            print "Layout not found. Manually create a new layout in '_layouts/' and try again."
    print ""

    categories = [f for f in os.listdir("content/") if os.path.isdir(os.path.join("content", f)) \
    and f.find("pages") < 0]
    for cat in categories:
        if cat != "pages":
            categories.extend([cat + "/" + f for f in os.listdir("content/" + cat + "/") \
                if os.path.isdir(os.path.join("content/" + cat + "/", f)) and f.find("pages") < 0])

    categories = sorted(categories)

    if verbose:
        print Color.header + "Categories:" + Color.normal, categories

    auto.createlist_completer(categories)
    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(auto.list_completer)

    while True:
        section = get_text("section: ")
        if section in categories:
            break
        else:
            print "section not found. Manually create a new folder in 'content/' and try again."

    print ""

    while len(title) < 8:
        title = get_text("Title: ")

    permalink = get_text("Permalink: ")
    author = get_text("Author name: ")

    filename = datetime.now().strftime("%Y-%m-%d") + "-" + title.lower().replace(" ", "-")

    frontmatter = {
        "layout": layout,
        "title": title,
        "date": datetime.now(tzlocal()).isoformat(),
        "author": author,
        "categories": section.split("/"),
        "permalink": permalink
    }
    if permalink == "":
        del frontmatter["permalink"]
    if author == "":
        del frontmatter["author"]

    newfile = open("content/" + section + "/" + filename + ".md", 'w')
    newfile.write("---\n")
    yaml.safe_dump(frontmatter, newfile, default_flow_style=False, indent=4)
    newfile.write("---\n\n")
    newfile.close()

    os.system(settings["editor"] + " " + "content/" + section + "/" + filename + ".md")
    return 0

def edit_post(settings, verbose, offset_min):
    '''
    edit a post in content/
    - search for a post by filename/title using autocomplete
    - search for a file by url (TODO)
    - updates post.frontmatter.modified by adding offset_min minutes to it
    '''
    def get_text(msg):
        ''' override the raw_input() with colored message '''
        return raw_input(Color.bold + Color.blue + msg + Color.normal)

    search_type = 0
    filename = ""

    try:
        search_type = get_text("Search posts by \n\t[0] filename (default)\n\t[1] title\n>> ")
        if not search_type:
            raise ValueError('no input specified')
    except ValueError:
        print "searching by file name"

    if search_type == 2:
        # under development.
        # enter url to find posts that are published and edit
        pass
    elif search_type == 1:
        print Color.yellow + "gathering files by titles..." + Color.normal,
        grep_titles = subprocess.check_output("grep -r 'title:'  content/ --exclude='index.html' \
            --exclude-dir=pages", shell=True).split("\n")
        print Color.yellow + "\b." + Color.normal,
        file_title = {}
        try:
            for gr_titles in grep_titles:
                gr_title = gr_titles.split(":")
                file_title[gr_title[2].strip().lstrip('"').rstrip('"')] = gr_title[0]
        except IndexError:
            pass
        titles = sorted(file_title.keys())
        print Color.yellow + "\b." + Color.normal, "found", len(titles), "posts"
        if verbose:
            print titles
        auto = AutoComplete()
        auto.createlist_completer(titles)
        readline.set_completer_delims('\t')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(auto.list_completer)
        while True:
            title = get_text("Title : ")
            try:
                filename = file_title[title]
                break
            except KeyError:
                print Color.error + "Could not find the desired file by title. Try again." \
                + Color.normal

    else:
        print Color.yellow + "gathering files..." + Color.normal,
        file_struct = [f for f in os.walk("content/")]
        print Color.yellow + "\b." + Color.normal,
        posts = []
        for files in file_struct:
            for filepath in files[2]:
                if "pages" not in files[0] and "index.html" not in filepath:
                    posts.append(files[0] + "/" + filepath)
        print "found " + str(len(posts)) + " posts"
        if verbose:
            print posts
        auto.createlist_completer(posts)
        readline.set_completer_delims('\t')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(auto.list_completer)
        print Color.yellow + "done." + Color.normal
        filename = get_text("File name : ")

    try:
        post = open(filename, 'r+')
        print "good file!"
    except IOError:
        print Color.error + "could not find the desired file. Try again." + Color.normal
        edit_post(settings, verbose, offset_min)

    lines = post.readlines() # to update post:modified time
    post.close()

    is_first = True
    for line in lines:
        if "---" in line and not is_first:
            line = "modified: " + str((datetime.now(tzlocal()) + \
             timedelta(minutes=offset_min)).isoformat()) + \
             "\n---\n" # if no "modified" in frontmatter
            break
        elif "modified" in line:
            line = "modified: " + str((datetime.now(tzlocal()) +\
             timedelta(minutes=offset_min)).isoformat()) + "\n" # updated modified
            break
        is_first = False

    postfile = open(filename, "w")
    postfile.writelines(lines)
    postfile.close()

    os.system(settings["editor"] + " " + filename)

    return

def git_backup(arg):
    ''' backup and restore public folders using git '''
    if arg == "backup":
        pass
    elif arg == "revert":
        pass

def manage_comments():
    '''
    comment helper
    '''
    def moderate():
        '''
        moderate comments (from "pending" sheet)
        - opens a localserver port for moderation panel
        '''
        print Color.yellow + "moderating comments" + Color.normal
        local_server("helper_comments")

    def publish():
        '''
        saves moderated comments (from "waiting" sheet) to local files
        '''
        from sys import path as syspath
        if "helper_comments" in os.getcwd():
            syspath.append(os.getcwd() + "/")
        else:
            syspath.append(os.getcwd() + "/helper_comments/")
        import comments_publish
        if "helper_comments" in os.getcwd():
            os.chdir("..")
        comments_publish.main()

    print Color.yellow + '''
    1. Open your Web browser at url given below to moderate comments.
    2. Click Submit after allowing/deleting comments.
    3. Kill local server here.
    4. And press [y] here to add comments to files.
    ''' + Color.normal
    moderate()
    if raw_input("Type 'y' to add comments, anything else to leave: ") == "y":
        publish()


def main():
    '''
    main function for helper
    - contains settings as dict
    - parses command line arguments
    read documentation for settings
    '''
    deployment_methods = {
        "git":
            """
            git add -A;
            git commit -m "backup";
            git push origin master;
            """,
        "git_p": "",
        "gae": "appcfg.py update .",
        "s3": ""
    }

    settings = {
        # read documentation for settings
        "editor": "subl", # gedit/subl or any other editor's command line name
        "offset_min": 10,
        "siteurl": "http://example.com/",
        "homepage": "each, 5" # coming soon, more features
    }

    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--verbose", help="verbose additional messages", \
        action='store_true')
    parser.add_argument("-c", "--category", help="build posts under given section", \
        nargs='*', type=str)
    parser.add_argument("--home", help="build home page", \
        action='store_true')
    parser.add_argument("-n", "--new", help="create new post", \
        action='store_true')
    parser.add_argument("-e", "--edit", help="edit a post", \
        action='store_true')
    parser.add_argument("-a", "--assets", help="build static assets", \
        action='store_true')
    parser.add_argument("-p", "--pages", help="build static pages", \
        action='store_true')
    parser.add_argument("-s", "--sitemap", help="build website sitemap", \
        action='store_true')
    parser.add_argument("-f", "--fresh", help="start a fresh build, clears public folder", \
        action='store_true')
    parser.add_argument("-l", "--local", help="show public folder on local server", \
        action='store_true')
    parser.add_argument("-g", "--git", help="backup and restore", \
        type=str, nargs=1, choices=["save", "revert"])
    parser.add_argument("--comments", help="manage comments and replies", \
        action='store_true')
    parser.add_argument("-d", "--deploy", help="deploy public directory. {deployment_methods}", \
        type=str, nargs='+', choices=deployment_methods.keys())
    args = parser.parse_args()

    if args.comments:
        manage_comments()

    if args.git:
        git_backup(args.git)
    if args.fresh:
        clear_public()
    if args.category == [] or args.category:
        create_category(args.category, args.verbose)
    if args.home:
        create_home_page(settings["homepage"], args.verbose)
    if args.pages:
        create_pages(args.verbose)
    if args.new:
        create_post(settings, args.verbose)
    if args.edit:
        edit_post(settings, args.verbose, settings["offset_min"])
    if args.sitemap:
        create_sitemap(settings["siteurl"])
    if args.assets:
        create_assets(args.verbose)
    if args.local:
        local_server("public")
    if args.deploy:
        deploy(args.deploy, deployment_methods)

    print Color.green + Color.bold + "Done." + Color.normal

if __name__ == '__main__':
    main()
