from . import AbstractPlugin
from django.http import JsonResponse

import operator


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

    def __init__(self, config):
        super().__init__(config)

        self.qs = [
            ('city', 'Nom de la commune', 'string'),
            ('date_gte', 'Plus récent que la date indiquée', 'date'),
            ('date_lte', 'Plus ancien que la date indiquée', 'date'),
            ('from', 'Index de pagination', 'integer'),
            ('group_by', "Champ d'aggregation", 'string'),
            ('resource', 'Nom de la resource', 'string'),
            ('size', 'Nombre max de résultats à retourner', 'integer'),
            ('sort_by', 'Trier les résultats', 'string'),
            ('source', 'Nom de la source de données', 'string'),
            ('suggest', 'Activer la suggestion', 'boolean'),
            ('suggest_mode', 'Mode de suggestion', 'string'),
            ('text', 'Texte à rechercher dans le document', 'string'),
            ('title', 'Texte à rechercher dans le titre', 'string')]

        self.opts = dict((e[0], None) for e in self.qs)

    @property
    def query_dsl(self):

        opts = self.opts

        data = {
            '_source': [
                'origin.filename', 'origin.resource.name',
                'origin.source.name', 'properties.*'],
            'from': opts['from'] or 0,
            'highlight': {'fields': {}, 'require_field_match': False},
            'query': {'bool': {}},
            'size': opts['size'] or 10,
            'suggest': {}}

        if opts['text']:
            data['query']['bool'] = {
                                'must': {
                                    'match': {
                                        'attachment.content': {
                                            'fuzziness': 'auto',
                                            'minimum_should_match': '75%',
                                            'query': opts['text']}}},
                                'should': {
                                    'match_phrase': {
                                        'attachment.content': {
                                            'query': opts['text'],
                                            'slop': 6}}}}

            data['highlight']['fields']['attachment.content'] = {
                                                    'post_tags': ['</strong>'],
                                                    'pre_tags': ['<strong>'],
                                                    'type': 'plain'}

        if opts['title']:
            data['query']['bool'].update({
                                'should': {
                                    'match': {
                                        'properties.titre': {
                                            'fuzziness': 'auto',
                                            'minimum_should_match': '75%',
                                            'query': opts['title']}}}})

            data['highlight']['fields']['properties.titre'] = {
                                                    'post_tags': ['</strong>'],
                                                    'pre_tags': ['<strong>'],
                                                    'type': 'plain'}

        filter = []
        if opts['source']:
            filter.append({'term': {'origin.source.name': opts['source']}})

        if opts['resource']:
            filter.append({'term': {'origin.resource.name': opts['resource']}})

        if opts['city']:
            filter.append({'term': {'properties.communes': opts['city']}})

        filter_range = {}
        if opts['date_gte']:
            filter_range.update({
                'range': {'properties.date_seance': {'gte': opts['date_gte']}}})
        if opts['date_lte']:
            filter_range.update({
                'range': {'properties.date_seance': {'lte': opts['date_lte']}}})
        if filter_range:
            filter.append(filter_range)

        if len(filter) > 0:
            data['query']['bool']['filter'] = filter

        if opts['sort_by']:
            prop = opts['sort_by']
            sort = 'asc'
            if prop.startswith('-'):
                prop = prop[1:]
                sort = 'desc'
            data['sort'] = {'properties.{0}'.format(prop): sort}

        if opts['group_by']:
            data['aggregations'] = {}
            data['aggregations'][opts['group_by']] = {
                                'terms': {
                                    'field': opts['group_by']}}

        # term suggester
        if opts['suggest'] and str(opts['suggest']).lower() in ('true', 't'):
            k_prop = {'text': 'attachment.content', 'title': 'properties.titre'}
            for k, prop in k_prop.items():
                if opts[k]:
                    if opts['suggest_mode'] == 'term':
                        data['suggest'].update({
                                    k: {'term': {'field': prop,
                                                 'size': 5,
                                                 'sort': 'frequency',
                                                 'suggest_mode': 'always'},
                                        'text': opts[k]}})
        return data

    def input(self, **params):
        self.opts.update(params)
        if not self.config:
            return self.query_dsl
        else:
            return self.config

    def output(self, data, **params):
        results = []
        for hit in data['hits']['hits']:
            entry = {'file': hit['_source']['origin']['filename'],
                     'resource': hit['_source']['origin']['resource']['name'],
                     'source': hit['_source']['origin']['source']['name']}

            if 'properties' in hit['_source'] and hit['_source']['properties']:
                entry['properties'] = hit['_source']['properties']

            if 'highlight' in hit:
                k_prop = {'text': 'attachment.content',
                          'title':'properties.titre'}
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

        if 'suggest' in data and isinstance(data['suggest'], dict):
            response['suggestions'] = {}

            for k, sub in data['suggest'].items():
                offset = {}
                for e in sub:
                    offset[e['offset']] = []
                    for opt in e['options']:
                        offset[e['offset']].append(opt['text'])

                lst = concatenator(
                        sorted(offset.items(), key=operator.itemgetter(0)), [])

                response['suggestions'].update({k: lst})

        return JsonResponse(response)


plugin = Plugin
