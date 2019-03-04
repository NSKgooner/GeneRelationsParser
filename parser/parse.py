import json
import re


class Parser(object):

    def __init__(self, path_abstracts='abstracts.json', path_pairs='gene_pairs.json'):
        self.path_abstracts = path_abstracts
        self.path_pairs = path_pairs

    @staticmethod
    def load_file(path):
        with open(path, 'r') as f:
            data = json.load(f)
        return data

    def get_abstract(self, id):
        return re.sub('Objective', '', self.load_file(self.path_abstracts)[str(id)]['abstract'])

    def get_genes(self, id):
        return self.load_file(self.path_pairs)[str(id)]['genes']

    def list_ids(self):
        ids = []
        for id in self.load_file(self.path_abstracts):
            ids.append(id)
        return ids

    def parse_json(self, id):
        genes = []
        for i in range(1, 10):
            try:
                genes.append(self.get_genes(id)['pair_' + str(i)]['gene_1_name'])
            except KeyError:
                break
        return genes
