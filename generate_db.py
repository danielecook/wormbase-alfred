import urllib2
import StringIO
import gzip
import sqlite3
import os

# Generate a database of gene ids and orthologs

# Remove database if it exists
if os.path.exists("wb.db"):
    os.remove("wb.db")

conn = sqlite3.connect('wb.db')

URL = "ftp://ftp.wormbase.org/pub/wormbase/species/c_elegans/annotation/geneIDs/c_elegans.PRJNA13758.current.geneIDs.txt.gz"

response = urllib2.urlopen(URL)
compressedFile = StringIO.StringIO()
compressedFile.write(response.read())
compressedFile.seek(0)
decompressedFile = gzip.GzipFile(fileobj=compressedFile, mode='rb').read()
genes = [x.split(",")[1:] for x in decompressedFile.splitlines()]

# Generate match name. 
for row in genes:
    if row[1] != "":
        row += [row[1]]
    elif row[2] != "":
        row += [row[2]]
    else:
        row += [row[0]]

c = conn.cursor()

# Create table
c.execute('''CREATE VIRTUAL TABLE idset using
             fts3(WBID,sequence,gene,live,match);''')

# Insert genes
c.executemany('INSERT INTO idset VALUES (?,?,?,?,?);', genes)

#
# WBGeneID \t PublicName \n
# Species \t Ortholog \t Public_name \t MethodsUsedToAssignOrtholog \n
#
# Load Ortholog Database
URL = "ftp://ftp.wormbase.org/pub/wormbase/species/c_elegans/annotation/orthologs/c_elegans.PRJNA13758.current.orthologs.txt.gz"

response = urllib2.urlopen(URL)
compressedFile = StringIO.StringIO()
compressedFile.write(response.read())
compressedFile.seek(0)
decompressedFile = gzip.GzipFile(fileobj=compressedFile, mode='rb').read().split("=\n")[1:]
#genes = [x.split("\n")[1:] for x in decompressedFile]
splitgroup = [x.splitlines() for x in decompressedFile]
orthodb = []
for i in splitgroup:
	WBID, gene = i[0].split("\t")
	orthodb.append([WBID, gene] + i[2].split("\t"))

# Create table
c.execute('''CREATE VIRTUAL TABLE orthodb using
             fts3(WBID,sequence,species,ortholog, ortholog_name,method_to_assign);''')

# Insert genes
c.executemany('INSERT INTO orthodb VALUES (?,?,?,?,?,?);', orthodb)

conn.commit()
c.close()