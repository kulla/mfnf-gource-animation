# create_mfnf_git.py - script for saving the history of MFNF in a git repo
#
# Written in 2016 by Stephan Kulla ( http://kulla.me )
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along
# with this software. If not, see
# <http://creativecommons.org/publicdomain/zero/1.0/>.

import os
import requests
import re
import shutil

from datetime import datetime
from subprocess import check_call

API_URL="https://de.wikibooks.org/w/api.php"

def query_path(obj, path_to_result):
    for key in path_to_result:
        if callable(key):
            obj = key(obj)
        else:
            obj = obj[key]

    return obj

def merge_obj(obj1, obj2):
    if obj1 == None:
        obj1 = obj2
    elif isinstance(obj1, list):
        obj1.extend(obj2)
    elif isinstance(obj1, dict):
        obj1.update(obj2)
    else:
        assert False

    return obj1

def query(params, path_to_result):
    params["action"] = "query"
    params["format"] = "json"
    result = None

    while True:
        api_result = requests.get(API_URL, params=params).json()
        result = merge_obj(result, query_path(api_result, path_to_result))

        if "continue" in api_result:
            params.update(api_result["continue"])
        else:
            return result

def revision_content(title, revid=None):
    params = {
        "prop": "revisions",
        "rvprop": "content|timestamp|user",
        "titles": title
    }

    if revid != None:
        params["rvstartid"] = revid
        params["rvendid"] = revid

    return query(params, ["query", "pages",
        lambda x: next(iter(x.values())), "revisions", 0, "*"])

def revisions(title):
    result = query({
        "prop": "revisions",
        "rvprop": "ids|timestamp|user|comment",
        "rvlimit": 500,
        "titles": title,
        "rvdir": "newer"
    }, ["query", "pages", lambda x: next(iter(x.values()))])

    if "revisions" in result:
        return result["revisions"]
    else:
        return []

class Node(object):
    def __init__(self, node_link, node_name,
            node_type=-1, node_level=-1):
        self._type = node_type
        self._level = node_level
        self.link = node_link
        self.name = node_name
        self.parent = None
        self.children = []

    def is_over(self, other_node):
        if self._type != other_node._type:
            return self._type < other_node._type
        else:
            return self._level < other_node._level

    def add_node(self, other_node):
        if len(self.children) > 0:
            last_child = self.children[-1]
        else:
            last_child = None

        if (last_child == None or
                (self.is_over(other_node) and not
                last_child.is_over(other_node))):
            self.children.append(other_node)
            other_node.parent = self
        else:
            last_child.add_node(other_node)

    def is_article(self):
        return len(self.children) == 0 and self.link

    def print_tree(self, level=0):
        print("  " * level + self.name)

        for child in self.children:
            child.print_tree(level+1)

    def clone_to_git(self, gitdir):
        shutil.rmtree(gitdir, ignore_errors=True)
        os.mkdir(gitdir)
        os.chdir(gitdir) # TODO: change to old cwd
        check_call(["git", "init"])

        revs = list(self.revisions())
        revs.sort(key = lambda x: x["date"])

        for rev in revs:
            git_add_rev(rev)

    @property
    def target_file_id(self):
        file_id = self.name

        if self.parent != None and self.parent.parent != None:
            file_id = os.path.join(self.parent.target_file_id, file_id)

        return file_id

    @property
    def target_file(self):
        return "%s.txt" % self.target_file_id

    def revisions(self):
        if self.link and not self.name.startswith("PDF-Version") and len(self.children) == 0:
            for rev in revisions(self.link):
                rev["target"] = self.target_file
                rev["title"] = self.name
                rev["date"] = datetime.strptime(rev["timestamp"], "%Y-%m-%dT%H:%M:%SZ")

                yield rev

        for child in self.children:
            yield from child.revisions()

def git_add_rev(rev):
    dirname = os.path.dirname(rev["target"])

    if len(dirname) > 0:
        os.makedirs(dirname, exist_ok=True)

        with open(rev["target"], "w") as fd:
            #fd.write(revision_content(self.link, rev["revid"]))
            fd.write(str(rev["revid"]))

        check_call(["git", "add", rev["target"]])

        date = rev["timestamp"].rstrip("Z")
        user = rev["user"]
        comment = rev["comment"].replace("'", "")

        check_call(
            "GIT_COMMITTER_DATE='%s' git commit --allow-empty-message -m '%s' --author '%s <%s@wikibooks>' --date '%s'" %(date, comment, user, user, date), shell=True)

def read_nodes(sitemap_text):
    for line in sitemap_text.splitlines():
        if line.startswith(("=", "*")):
            node_type = line[0]
            node_level = len(line) - len(line.lstrip(node_type))

            if node_type == "=":
                line = line.strip(node_type)
            else:
                line = line.lstrip(node_type)

            line = line.strip()
            line = re.sub("\s+{{Symbol\|\d+%}}", "", line)

            node_name = line
            node_link = None

            if line.startswith("[[") and line.endswith("]]"):
                line = line.lstrip("[").rstrip("]")

                i = line.index("|")

                node_link = line[:i]
                node_name = line[i+1:] 

            yield Node(node_link, node_name,
                       0 if node_type == "=" else 1, node_level)

PROJECT="Mathe für Nicht-Freaks"
SITEMAP=PROJECT + ": Sitemap"
def parse_sitemap():
    result = Node(PROJECT, PROJECT)

    for node in read_nodes(revision_content(SITEMAP)):
        result.add_node(node)

    return result

if __name__ == "__main__":
    git_dir = os.path.join(os.path.dirname(__file__), "git")

    sitemap = parse_sitemap()
    sitemap.clone_to_git(git_dir)
    #print(revisions("Mathe für Nicht-Freaks: Grundlagen der Mathematik"))
