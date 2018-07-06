from . import AbstractPlugin

from django.conf import settings
from django.http import JsonResponse

import operator
import re


try:
    PDF_BASE_DIR = 'file://{0}'.format(settings.PDF_DATA_BASE_DIR)
except AttributeError:
    PDF_BASE_DIR = 'file://'


def concatenator(offset, m):
    if len(offset) == 0:
        return [e.rstrip() for e in m]
    for i in range(len(offset)):
        entry = offset.pop(i)
        options = entry[1]
        if len(m) == 0:
            return concatenator(offset, ['{0} '.format(e) for e in options])
        new_m = []
        for word in m:
            if options:
                for e in options:
                    new_m.append('{0}{1} '.format(word, e))
            else:
                return concatenator(offset, m)
        return concatenator(offset, new_m)


class Plugin(AbstractPlugin):

    def __init__(self, config, contexts, **kwargs):
        super().__init__(config, contexts, **kwargs)

        self.qs = [
            ('city', 'Nom de la commune', 'string'),
            ('date_gte', 'Plus récent que la date indiquée', 'date'),
            ('date_lte', 'Plus ancien que la date indiquée', 'date'),
            ('document_type', 'Type de document', 'string'),
            ('from', 'Index de pagination', 'integer'),
            ('group_by', "Champ d'aggregation", 'string'),
            ('resource', 'Nom de la resource', 'string'),
            ('size', 'Nombre max de résultats à retourner', 'integer'),
            ('sort_by', 'Trier les résultats', 'string'),
            ('source', 'Nom de la source de données', 'string'),
            ('session_id', 'Numéro de séance', 'string'),
            ('session_type', 'Type de séance', 'string'),
            # ('suggest', 'Activer la suggestion', 'boolean'),
            # ('suggest_mode', 'Mode de suggestion', 'string'),
            ('text', 'Texte à rechercher dans le document', 'string'),
            ('title', 'Texte à rechercher dans le titre', 'string')]

        self.opts = dict((e[0], None) for e in self.qs)

    def filepath(self, path):
        for context in self.contexts:
            if path.startswith(context.resource.name):
                return path[len(context.resource.name) + 1:]

    def get_source_directory(self, name):
        for context in self.contexts:
            if context.resource.source.name == name:
                uri = context.resource.source.uri
                return uri.startswith(PDF_BASE_DIR) and uri[len(PDF_BASE_DIR):] or uri

    def prop_is_text(self, name):
        for index, columns in self.columns_by_index.items():
            for column in columns:
                if column[0] == name and column[1] == 'text':
                    return True
        return False

    @property
    def query_dsl(self):

        opts = self.opts

        data = {
            '_source': [
                'origin.filename', 'origin.resource.name',
                'origin.source.name', 'properties.*'],
            'from': opts['from'] and opts['from'].pop() or 0,
            'highlight': {'fields': {}, 'require_field_match': False},
            'query': {'bool': {'must': [], 'must_not': [], 'should': []}},
            'size': opts['size'] and opts['size'].pop() or 10,
            # 'suggest': {}
            }

        must, must_not, should = [], [], []

        if opts['text']:
            must.append({
                'match': {
                    'attachment.content': {
                        'fuzziness': 'auto',
                        'minimum_should_match': '75%',
                        'query': ' '.join(opts['text'])}}})

            should.append({
                'match_phrase': {
                    'attachment.content': {
                        'query': ' '.join(opts['text']),
                        'slop': 6}}})

            data['highlight']['fields']['attachment.content'] = {
                'post_tags': ['</strong>'],
                'pre_tags': ['<strong>'],
                'type': 'plain'}

        if opts['title']:
            must.append({
                'match': {
                    'properties.titre': {
                        'fuzziness': 'auto',
                        'minimum_should_match': '75%',
                        'query': ' '.join(opts['title'])}}})

            data['highlight']['fields']['properties.titre'] = {
                'post_tags': ['</strong>'],
                'pre_tags': ['<strong>'],
                'type': 'plain'}

        def must_or_must_not(l):
            force, include, exclude = [], [], []
            for v in l:
                if v == '\exists':
                    force.append(v)
                elif v.startswith('!'):
                    exclude.append(v[1:])
                else:
                    include.append(v)
            return force, include, exclude

        must_clause_params = {
            'city': 'properties.communes',
            'document_type': 'properties.type_document',
            'resource': 'origin.resource.name',
            'session_id': 'properties.numero_seance',
            'session_type': 'properties.type_seance',
            'source': 'origin.source.name'}

        for param, field in must_clause_params.items():
            value = opts[param]
            if value and param == 'session_type' and '\\all' in value:
                should.append({
                    'bool': {
                        'must': [
                            {'exists': {'field': 'properties.type_seance'}}],
                        'must_not': [
                            {'regexp': {'properties.type_document': 'RAPPORT|PJ'}}]
                        }
                    })
                should.append({'match': {'properties.type_document': 'ARRETE'}})
                # opts.pop('document_type')
                # opts.pop('session_type')
            elif value:
                force, include, exclude = must_or_must_not(value)
                if force:
                    must.append({'exists': {'field': field}})
                if include:
                    must.append({'regexp': {field: '|'.join(
                        ['{}'.format(m) for m in include])}})
                if exclude:
                    must_not.append({'regexp': {field: '|'.join(
                        ['{}'.format(m) for m in exclude])}})

        range_date = {'range': {'properties.date_seance': {}}}

        rounding_down = \
            lambda str: {4: '||/y', 6: '||/M', 8: '||/d'}.get(len(str), '')

        if opts['date_gte']:
            prop = opts['date_gte'].pop()
            range_date['range']['properties.date_seance'].update({
                'gte': '{0}{1}'.format(prop, rounding_down(prop))})

        if opts['date_lte']:
            prop = opts['date_lte'].pop()
            range_date['range']['properties.date_seance'].update({
                'lte': '{0}{1}'.format(prop, rounding_down(prop))})

        must.append(range_date)

        if len(must) > 0:
            data['query']['bool']['must'] = must

        if len(must_not) > 0:
            data['query']['bool']['must_not'] = must_not

        if len(should) > 0:
            data['query']['bool']['should'] = should

        if opts['sort_by']:
            prop = opts['sort_by'].pop()
            sort = 'asc'
            if prop.startswith('-'):
                prop = prop[1:]
                sort = 'desc'
            prop = re.sub(
                '(properties\.)?(\w+)(\.keyword)?',
                'properties.\g<2>{0}'.format(
                    self.prop_is_text(prop) and '.keyword' or ''), prop)
            data['sort'] = {prop: sort}

        if opts['group_by']:
            prop = opts['group_by'].pop()
            data['aggregations'] = {}
            data['aggregations'][prop] = {'term': {'field': prop}}

        # TODO term suggester
        # if opts['suggest'] and str(opts['suggest']).lower() in ('true', 't'):
        #     k_prop = {'text': 'attachment.content',
        #               'title': 'properties.titre'}
        #     for k, prop in k_prop.items():
        #         if opts[k]:
        #             if opts['suggest_mode'] == 'term':
        #                 data['suggest'].update({
        #                     k: {'term': {'field': prop,
        #                                  'size': 5,
        #                                  'sort': 'frequency',
        #                                  'suggest_mode': 'always'},
        #                         'text': opts[k]}})
        return data

    def input(self, **params):
        self.opts.update(dict((k, v.split(',')) for k, v in params.items()))
        if not self.config:
            return self.query_dsl
        else:
            return self.config

    def output(self, data, **params):

        def get_type_document_seance(document, seance):
            if not document or not seance:
                return None
            if document.startswith('A') and seance.startswith('B'):
                return 'Annexe de la décision'
            if document.startswith('D') and seance.startswith('B'):
                return 'Décision'
            if document.startswith('A') and seance.startswith('C'):
                return 'Annexe de la délibération'
            if document.startswith('D') and seance.startswith('C'):
                return 'Délibération'
            if document.startswith('AR') and seance.startswith('A'):
                return 'Arrêté'
            if document.startswith('AN') and seance.startswith('A'):
                return "Annexe de l'arrêté"

        results = []
        for hit in data['hits']['hits']:
            entry = {
                'file': self.filepath(hit['_source']['origin']['filename']),
                'resource': hit['_source']['origin']['resource']['name'],
                'source': self.get_source_directory(
                    hit['_source']['origin']['source']['name'])}

            if 'properties' in hit['_source'] and hit['_source']['properties']:
                entry['properties'] = hit['_source']['properties']

                entry['extras'] = {
                    'type_document_seance': get_type_document_seance(
                        hit['_source']['properties'].get('type_document'),
                        hit['_source']['properties'].get('type_seance'))}

            if 'highlight' in hit:
                k_prop = {'text': 'attachment.content',
                          'title': 'properties.titre'}
                for k, prop in k_prop.items():
                    if prop in hit['highlight']:
                        v = hit['highlight'][prop]
                        entry.update({
                            'highlight': {k: (len(v) > 1) and v or v[0]}})

            results.append(entry)

        response = {'results': results,
                    'total': data['hits']['total']}

        if 'aggregations' in data:
            # response['aggregations'] = \
            #             data['aggregations'][self.opts['group_by']]['buckets']
            response['aggregations'] = data['aggregations']

        # if 'suggest' in data and isinstance(data['suggest'], dict):
        #     response['suggestions'] = {}
        #
        #     for k, sub in data['suggest'].items():
        #         offset = {}
        #         for e in sub:
        #             offset[e['offset']] = []
        #             for opt in e['options']:
        #                 offset[e['offset']].append(opt['text'])
        #
        #         lst = concatenator(
        #             sorted(offset.items(), key=operator.itemgetter(0)), [])
        #
        #         response['suggestions'].update({k: lst})

        return JsonResponse(response)


plugin = Plugin
