#!/usr/bin/env python

"""
A simple Python wrapper for the stanford IE binary that makes it easier to use it
on UNIX/Windows systems.
Note: The script does some minimal sanity checking of the input, but don't
    expect it to cover all cases. After all, it is a just a wrapper.
Example:
    > echo "Barack Obama was born in Hawaii." > text.txt
    > python main.py -f text.txt
    > python main.py -f text.txt,text2.txt (for batch mode).
    Should display
    1.000: (Barack Obama; was; born)
    1.000: (Barack Obama; was born in; Hawaii)
Authors:    Philippe Remy       <github: philipperemy>
Version:    2016-07-08
"""

# Copyright (c) 2016, Philippe Remy <github: philipperemy>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from __future__ import print_function

import os
import re
import nltk
import json
import numpy as np

from argparse import ArgumentParser
from subprocess import Popen
from sys import argv
from sys import stderr
from nltk.corpus import stopwords
from parser import parse

JAVA_BIN_PATH = 'java'
DOT_BIN_PATH = 'dot'
STANFORD_IE_FOLDER = 'stanford-openie'

tmp_folder = '/tmp/openie/'
if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)

img_folder = 'img/'
if not os.path.exists(img_folder):
    os.makedirs(img_folder)


def arg_parse():
    arg_p = ArgumentParser('Stanford IE Python Wrapper')
    arg_p.add_argument('-f', '--filename', type=str, default=None)
    arg_p.add_argument('-v', '--verbose', action='store_true')
    arg_p.add_argument('-g', '--generate_graph', action='store_true')
    return arg_p


def debug_print(log, verbose):
    if verbose:
        print(log)


def process_entity_relations(entity_relations_str, verbose=True):
    # format is ollie.
    entity_relations = list()
    for s in entity_relations_str:
        entity_relations.append(s[s.find("(") + 1:s.find(")")].split(';'))
    return entity_relations


def generate_graphviz_graph(entity_relations, verbose=True):
    """digraph G {
    # a -> b [ label="a to b" ];
    # b -> c [ label="another label"];
    }"""
    graph = list()
    graph.append('digraph {')
    for er in entity_relations:
        graph.append('"{}" -> "{}" [ label="{}" ];'.format(er[0], er[2], er[1]))
    graph.append('}')

    out_dot = tmp_folder + 'out.dot'
    with open(out_dot, 'w') as output_file:
        output_file.writelines(graph)

    out_png = img_folder + 'out.png'
    command = '{} -Tpng {} -o {}'.format(DOT_BIN_PATH, out_dot, out_png)
    debug_print('Executing command = {}'.format(command), verbose)
    dot_process = Popen(command, stdout=stderr, shell=True)
    dot_process.wait()
    assert not dot_process.returncode, 'ERROR: Call to dot exited with a non-zero code status.'
    print('Wrote graph to {} and {}'.format(out_dot, out_png))


def stanford_ie(input_filename, verbose=False, generate_graphviz=False):
    out = tmp_folder + 'out.txt'
    input_filename = input_filename.replace(',', ' ')

    new_filename = ''
    for filename in input_filename.split():
        if filename.startswith('/'):  # absolute path.
            new_filename += '{} '.format(filename)
        else:
            new_filename += '../{} '.format(filename)

    absolute_path_to_script = os.path.dirname(os.path.realpath(__file__)) + '/'
    command = 'cd {};'.format(absolute_path_to_script)
    command += 'cd {}; {} -mx4g -cp "stanford-openie.jar:stanford-openie-models.jar:lib/*" ' \
               'edu.stanford.nlp.naturalli.OpenIE {} -format ollie > {}'. \
        format(STANFORD_IE_FOLDER, JAVA_BIN_PATH, new_filename, out)

    if verbose:
        debug_print('Executing command = {}'.format(command), verbose)
        java_process = Popen(command, stdout=stderr, shell=True)
    else:
        java_process = Popen(command, stdout=stderr, stderr=open(os.devnull, 'w'), shell=True)
    java_process.wait()
    assert not java_process.returncode, 'ERROR: Call to stanford_ie exited with a non-zero code status.'

    with open(out, 'r') as output_file:
        results_str = output_file.readlines()
    os.remove(out)
    results = process_entity_relations(results_str, verbose)
    if generate_graphviz:
        generate_graphviz_graph(results, verbose)

    return results


def drop_stopwords(sentence):
    """

    :param sentence:
    :return: sentence without stop words (str)
    """
    # punct = re.compile(
    #    '[\\!\\"\\#\\$\\&\\\'\\(\\)\\*\\+\\,\\-\\.\\/\\:\\;\\<\\=\\>\\?\\@\\[\\\\\\]\\^_\\`\\{\\|\\}\\~]', 0)
    # return punct.sub(' ', sentence.lower())
    stop_words = stopwords.words('english')
    stop_words = [elem for elem in stop_words if elem not in ['and']]
    not_stop = [word for word in sentence.split() if word not in stop_words]
    return ' '.join(not_stop).lower()


def decode_alpha(word):
    """
    drop alpha and beta (doesn't work now)
    :param word:
    :return:
    """
    return re.sub("\u03B1", "alpha", word)


def normalize(sentence):
    """
    doesn't use it
    """
    # porter = PorterStemmer()

    stop_words = stopwords.words('english')
    not_stop = [word for word in sentence.split() if word not in stop_words]
    # return ' '.join([porter.stem(word) for word in not_stop])
    return not_stop


def group(genes, entities):
    """
    create lists for each gene relations

    :param genes:
    :param entities:
    :return:
    """
    genes_relations = []
    for gen in genes:
        genes_relations.append(list(filter(lambda x: x[0] == gen, entities)))

    return genes_relations


def match(groups):
    """
    choose one relations for each activity type
    now it's choosing by len of third part, in the future it's classification (ranging) task
    :param groups:
    :return:
    """
    matches = []
    for group in groups:
        matches.append(group[(np.argmax(list(map(lambda x: len(x[2]), group))))])
    return matches


def main(args):
    nltk.download('stopwords')  # download stopwords for nltk
    parser = parse.Parser()  # init parser
    ids = parser.list_ids()  # get abstracts id
    data = []
    for id in ids[:2]:
        try:
            abstract = drop_stopwords(parser.get_abstract(id))
            genes_list = [drop_stopwords(elem) for elem in parser.parse_json(id)]
            with open('samples.txt', 'w') as f:  # write abstract to file for launch it from command line
                                                # BAD part need to change it
                f.write(abstract)
            arg_p = arg_parse().parse_args(args[1:])
            filename = arg_p.filename
            verbose = arg_p.verbose
            # something from original stanfords code

            if filename is None:
                print('please provide a text file containing your input. Program will exit.')
                exit(1)
            if verbose:
                debug_print('filename = {}'.format(filename), verbose)

            entities_relations = stanford_ie(filename)  # main part

            try:
                entities_relations = [elem for elem in entities_relations if elem[0] in genes_list]
                set_genes = list(set([elem[0] for elem in entities_relations]))
                data.append({'id': id, 'abstract': abstract, 'genes': genes_list, 'gen': set_genes,
                             'match': match(group(set_genes, entities_relations))})
            except ValueError:
                data.append({'id': 'no relations'})
        except KeyError:
            data.append({'id': 'no data'})

    with open('relations_3000.json', 'w') as f:
        json.dump(data, f)


if __name__ == '__main__':
    exit(main(argv))
