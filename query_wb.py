#!/usr/bin/python
# encoding: utf-8

import sys
import re

from workflow import Workflow, web
import sqlite3
import urllib2
import json
import difflib

log = None

def rest(url):
    base = "http://api.wormbase.org/rest/field/"
    req = urllib2.Request(base + url)
    req.add_header("Content-Type","application/json")
    resp = urllib2.urlopen(req)
    content = json.loads(resp.read())
    return content


def main(wf):
    args = wf.args[0].strip()
    log.debug(args)
    conn = sqlite3.connect('wb.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    q = '''SELECT * FROM idset WHERE idset MATCH "{q}*" ORDER BY sequence ASC LIMIT 50 '''.format(q=args)
    c.execute(q)
    rows = c.fetchall()

    #log.debug(a)

    # Exact hit?
    row_match = [x for x in rows if x["match"] == args]

    if len(rows) >= 1 and len(row_match) != 1:
        # Display search results
        rows = sorted(rows, key=lambda x: difflib.SequenceMatcher(None, x["match"], args).ratio(), reverse=True)
        for row in rows:
            wf.add_item(row["match"],row["WBID"], autocomplete=row["match"], valid=False, icon="icon.png")
    elif row_match == 1 and len(row_match) != 1:
        # Have user input changed to match column
        row = rows[0]
        wf.add_item(row["match"],row["WBID"], autocomplete=row["match"], valid=False, icon="icon.png")
    elif len(row_match) == 1:
        row = row_match[0]
        if row["live"] == "Dead":
            wf.add_item("Dead ID",row["match"], valid=False, icon="death.png")
        else:
            wormbase_url = "http://www.wormbase.org/species/c_elegans/gene/" + row["WBID"]
            wf.add_item(row["sequence"],"Public Name", arg=wormbase_url, copytext=row["sequence"], valid=True, icon="icon.png")
            wf.add_item(row["gene"],"Gene Name", arg=wormbase_url, copytext=row["gene"], valid=True, icon="icon.png")
            wf.add_item(row["WBID"],"Wormbase ID", arg=wormbase_url, copytext=row["WBID"], valid=True, icon="icon.png")
            # Position
            pos = rest("gene/{WBID}/location".format(WBID=row[0]))
            pos = pos["location"]["genomic_position"]["data"][0]["label"]
            wormbrowse = "http://www.wormbase.org/tools/genome/gbrowse/c_elegans_PRJNA13758/?name=" + pos
            wf.add_item(pos,"Genomic Position", arg=wormbrowse, valid=True, icon="loc.png")

            # Description
            desc = rest("gene/{WBID}/concise_description".format(WBID=row[0]))
            desc = desc["concise_description"]["data"]["text"]
            wf.add_item(desc,"Description",  valid=False, icon="icon.png")

            # Orthologs
            q = '''SELECT * FROM orthodb WHERE WBID == "{WBID}" ORDER BY sequence ASC LIMIT 50 '''.format(WBID=row["WBID"])
            c.execute(q)
            ortho_set = c.fetchall()
            for ortholog in ortho_set:
                ortho_title = "{ortho_name} ({species})".format(ortho_name=ortholog["ortholog_name"], 
                                                                species = ortholog["species"])
                ortholog_link = "http://www.wormbase.org/db/get?name={ortholog};class=Gene".format(ortholog=ortholog["ortholog"])
                wf.add_item(ortho_title,"Ortholog - " + ortholog["ortholog"], arg=ortholog_link, copytext=ortho_title, valid=True, icon="ortholog.png")

            # Publications
            pub = rest("gene/{WBID}/references".format(WBID=row[0]))
            for i in pub["references"]["data"]:
                first_author = i["author"][0]["label"]
                pub_id = i["name"]["id"]
                colsep = ""
                try:
                    journal = i["journal"][0]
                except:
                    journal = ""
                try:
                    volume = i["volume"][0]
                except:
                    volume = ""
                try:
                    page = i["page"][0]
                    colsep = ":"
                except:
                    page = ""
                try:
                    year = i["year"]
                except:
                    year = "-"
                try:
                    title = i["title"][0]
                except:
                    title = ""


                URL = "http://www.wormbase.org/resources/paper/" + pub_id
                subtitle = "{first_author} et al. {journal} {volume}{colsep} {page} ({year})".format(**locals())
                wf.add_item(title, subtitle, arg=URL, valid=True, copytext=title, icon="document.png")



    else:
        wf.add_item("No Results", valid=False)

    wf.send_feedback()



if __name__ == '__main__':
    wf = Workflow()
    # Assign Workflow logger to a global variable, so all module
    # functions can access it without having to pass the Workflow
    # instance around
    log = wf.logger
    sys.exit(wf.run(main))

