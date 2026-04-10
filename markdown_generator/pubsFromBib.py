#!/usr/bin/env python
# coding: utf-8

# # Publications markdown generator for academicpages
# 
# Takes a set of bibtex of publications and converts them for use with [academicpages.github.io](academicpages.github.io). This is an interactive Jupyter notebook ([see more info here](http://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/what_is_jupyter.html)). 
# 
# The core python code is also in `pubsFromBibs.py`. 
# Run either from the `markdown_generator` folder after replacing updating the publist dictionary with:
# * bib file names
# * specific venue keys based on your bib file preferences
# * any specific pre-text for specific files
# * Collection Name (future feature)
# 
# TODO: Make this work with other databases of citations, 
# TODO: Merge this with the existing TSV parsing solution

from pybtex.database.input import bibtex
import pybtex.database.input.bibtex 
from time import strptime
import string
import html
import os
import re

publist = {
    "proceeding": {
        "file" : "conference.bib",
        "venuekey": "booktitle",
        "venue-pretext": "",
        "collection" : {"name":"publications",
                        "permalink":"/publication/"}
    },
    "journal":{
        "file": "journal.bib",
        "venuekey" : "journal",
        "venue-pretext" : "",
        "collection" : {"name":"publications",
                        "permalink":"/publication/"}
    },
    "preprint":{
        "file": "preprint.bib",
        "venuekey" : "howpublished",
        "venue-pretext" : "",
        "collection" : {"name":"publications",
                        "permalink":"/publication/"}
    }
}

CATEGORY_MAP = {
    "proceeding": "conferences",
    "journal": "journals",
    "preprint": "preprints"
}

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
}

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)


for pubsource in publist:
    parser = bibtex.Parser()
    bibdata = parser.parse_file(publist[pubsource]["file"])

    for bib_id in bibdata.entries:
        pub_year = "1900"
        pub_month = "01"
        pub_day = "01"
        
        b = bibdata.entries[bib_id].fields
        
        try:
            pub_year = f'{b["year"]}'

            if "month" in b.keys(): 
                if(len(b["month"])<3):
                    pub_month = "0"+b["month"]
                    pub_month = pub_month[-2:]
                elif(b["month"] not in range(12)):
                    tmnth = strptime(b["month"][:3],'%b').tm_mon   
                    pub_month = "{:02d}".format(tmnth) 
                else:
                    pub_month = str(b["month"])
            if "day" in b.keys(): 
                pub_day = str(b["day"])

            pub_date = pub_year+"-"+pub_month+"-"+pub_day
            
            clean_title = b["title"].replace("{", "").replace("}","").replace("\\","").replace(" ","-")    

            url_slug = re.sub("\\[.*\\]|[^a-zA-Z0-9_-]", "", clean_title)
            url_slug = url_slug.replace("--","-")

            md_filename = (str(pub_date) + "-" + url_slug + ".md").replace("--","-")
            html_filename = (str(pub_date) + "-" + url_slug).replace("--","-")

            # ── Build Authors string ───────────────────────────────────────────
            authors_list = []
            for author in bibdata.entries[bib_id].persons["author"]:
                first_name = author.first_names[0] if author.first_names else ""
                last_name  = author.last_names[0]  if author.last_names  else ""
                full_name  = f"{first_name} {last_name}".strip()
                if first_name == "Shibam" and last_name == "Ghosh":
                    full_name = "**Shibam Ghosh**"
                authors_list.append(full_name)
            authors = ", ".join(authors_list)
            # ──────────────────────────────────────────────────────────────────

            ## YAML front matter
            md = "---\ntitle: \"" + html_escape(b["title"].replace("{", "").replace("}","").replace("\\","")) + '"\n'
            
            md += "collection: " + publist[pubsource]["collection"]["name"]
            md += "\npermalink: " + publist[pubsource]["collection"]["permalink"] + html_filename
            md += "\ncategory: "  + CATEGORY_MAP.get(pubsource, "conferences") + "\n"

            note = False
            if "note" in b.keys():
                if len(str(b["note"])) > 5:
                    md += "\nexcerpt: '" + html_escape(b["note"]) + "'"
                    note = True

            md += "\ndate: " + str(pub_date)

            # ── Skip venue entirely for preprints ─────────────────────────────
            if pubsource != "preprint":
                venue = (publist[pubsource]["venue-pretext"]
                         + b[publist[pubsource]["venuekey"]]
                         .replace("{", "").replace("}","").replace("\\",""))
                md += "\nvenue: '" + html_escape(venue) + "'"
            # ──────────────────────────────────────────────────────────────────

            md += "\nauthors: '" + html_escape(authors) + "'"

            # ── Keep paperurl for "Access paper here" link ────────────────────
            if "url" in b.keys():
                if len(str(b["url"])) > 5:
                    md += "\npaperurl: '" + b["url"] + "'"
            # ──────────────────────────────────────────────────────────────────

            md += "\n---"

            ## Markdown body
            if note:
                md += "\n" + html_escape(b["note"]) + "\n"

            md_filename = os.path.basename(md_filename)

            with open("../_publications/" + md_filename, 'w', encoding="utf-8") as f:
                f.write(md)
            print(f'SUCESSFULLY PARSED {bib_id}: \"', b["title"][:60], "..."*(len(b['title'])>60), "\"")

        except KeyError as e:
            print(f'WARNING Missing Expected Field {e} from entry {bib_id}: \"', b["title"][:30], "..."*(len(b['title'])>30), "\"")
            continue
