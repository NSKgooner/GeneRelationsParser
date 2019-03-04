import os
import re

from parser import parse

parser = parse.Parser()
ids = parser.list_ids()
id = ids[102]

abstract = parser.get_abstract(id)
genes = parser.get_genes(id)

# gen = genes['pair_4']['gene_1_name']

with open('samples.txt', 'w') as f:
    # f.write(re.sub('DKK3', 'gene1', abstract))
    f.write(abstract)

print(parser.list_ids())
print(parser.parse_json(id))
print(abstract, genes)

os.system('python main.py -f samples.txt')
