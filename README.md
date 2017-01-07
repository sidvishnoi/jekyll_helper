This is a helper written in Python (2.7) for Jekyll, that helps you manage large Jekyll website.

## Features

* Helps you in partial builds with Jekyll. It picks up the "section" of website that you want to build and generates only that part - making the builds faster. This is done because you generally edit a single post - so why regenerate whole site for that? You can divide website into independent sub-sections. For example- static assets, home page, static pages, posts - posts in different categories.

* Integrated with a custom Jekyll comments system. Now you can add static comments to your HTML website.

* Create a new post. Create a new post with your favorite text editor. Front-matter is set and adjusted automatically.

* Check built website locally, local server powered by Python SimpleHTTPServer.

* Deploy generated website to your preferred host, like GAE or AWS.

* Edit a post. Search a post by title or file name (TODO : by URL) and edit it.

* Auto-predict in command line.

See details in [WIKI](https://github.com/sidvishnoi/jekyll_helper/wiki).

## Options

```

-h, --help            shows help message and exit

-v, --verbose         verbose additional messages

-c [CATEGORY [CATEGORY ...]], --category [CATEGORY [CATEGORY ...]]
                    build posts under given category

--home                build home page

-n, --new             create new post

-e, --edit            edit a post

-a, --assets          build static assets

-p, --pages           build static pages

-s, --sitemap         build website sitemap

-f, --fresh           start a fresh build, clears public folder

-l, --local           show public folder on local server

-g {save,revert}, --git {save,revert}
                    backup and restore

--comments            manage comments and replies

-d {git_p,s3,gae,git} [{git_p,s3,gae,git} ...], --deploy {git_p,s3,gae,git} [{git_p,s3,gae,git} ...]
                    deploy public directory. see deployment\_methods
```

See option details and setup details in [WIKI](https://github.com/sidvishnoi/jekyll_helper/wiki).


## Usage

``` bash
$ cd path/to/project/
$ python helper.py [OPTIONS]
```

## Contribute

This is just a sample script, made to share the ideas how to make the builds efficient. You can create your own methods, or contribute to make this one better.

This is currently being used on my blog (http://www.hoopsvilla.com).

Tested on Ubuntu 14.04 and 16.04.
