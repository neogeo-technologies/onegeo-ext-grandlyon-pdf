![Alt text](grandlyon_320x66.png)

# Extension de profil de recherche Onegeo __{pdf}__.py

Service de recherche des documents PDF RAAD et Lyvia du Grand Lyon.

## Configuration du service

### URL du service

[http://localhost/onegeo/api/profiles/__{pdf}__/search?](
    http://localhost/onegeo/api/profiles/pdf/search)

### Paramètres de chaîne de recherche

| Paramètre    | Type    | Description                          |
| ------------ | ------- | ------------------------------------ |
| city         | string  | Nom de la commune                    |
| date_gte     | date    | Plus récent que la date indiquée     |
| date_lte     | date    | Plus ancien que la date indiquée     |
| from         | integer | Index de pagination                  |
| group_by     | string  | Champ d'aggrégation                  |
| session_id   | string  | Numéro de la séance                  |
| session_type | string  | Type de la séance                    |
| size         | integer | Nombre de résultats à retourner      |
| sort_by      | string  | Champ de tri                         |
| suggest      | boolean | Activer la suggestion (expérimental) |
| suggest_mode | string  | Mode de suggestion (expérimental)    |
| text         | string  | Texte à rechercher dans le document  |
| title        | string  | Texte à rechercher dans le titre     |

#### Migration depuis l'ancien service de recherche PDF du GrandLyon

Cf. le [tableau de migration](/docs/migration.md) pour plus d'information.

#### Configuration dans l'interface d'administration de Onegeo

Cf. la [documentation d'administration des profils d'indexation et de
recherche](/docs/admin.md).

### Format des résultats

Le service retourne les résultats dans un document JSON.
Celui-ci est structuré de la façon suivante :

``` JSON
{
    "total": 123,
    "results": [
        { ... },
        { ... },
        { ... },
        { ... },
        { ... },
        { ... },
        { ... },
        { ... },
        { ... },
        { ... }
    ]
}
```

Et chaque résultat est structuré de la manière ci-dessous :

``` JSON
{
    "file": "chemin/vers/le/fichier.pdf",
    "resource": "nom_du_repertoire_de_la_ressource",
    "source": "nom_du_repertoire_de_la_source",
    "properties": { ... }
}
```

Le chemin complet du fichier est le résultat de la concaténation
des trois paramètres : __source__/__resource__/__file__.

Les propriétés (__properties__) correspondent aux attributs de métadonnées des
fichiers PDF définis dans les profils d'indexation de Onegeo pour chacune des
ressources configurées.

Les propriétés (__extras__) contiennent des attributs transformés issus des
attributs de métadonnées.

``` JSON
{
    "file": ...,
    "resource": ...,
    "source": ...,
    "properties": {
        "date_seance": ...,
        "communes": ...,
        "type_seance": ...,
        "type_document": ...,
        "numero_seance": ...,
        "titre": ...
    },
    "extras": {
        "get_type_document_seance": ...
    }
}
```

## Usages

### Paginer les résultats d'une requête

Par défaut, le service retourne les dix premiers résultats.
Les paramètres __from__ et __size__ permettent de paginer les résultats
de la manière suivante :

* [http://localhost/onegeo/api/profiles/__{pdf}__/search?__from__=__0__&__size__=__10__&..](
    http://localhost/onegeo/api/profiles/pdf/search?from=0&size=10) (valeurs par défaut)
* [http://localhost/onegeo/api/profiles/__{pdf}__/search?__from__=__10__&__size__=__10__&..](
    http://localhost/onegeo/api/profiles/pdf/search?from=10&size=10)
* [http://localhost/onegeo/api/profiles/__{pdf}__/search?__from__=__20__&__size__=__10__&..](
    http://localhost/onegeo/api/profiles/pdf/search?from=20&size=10)
* etc.

### Rechercher dans les contenus textuels des documents

Le paramètre __text__ permet d'effectuer une recherche textuelle dans le
contenu des documents PDF.

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__text__=__Texte à rechercher__](
    http://localhost/onegeo/api/profiles/pdf/search?text=Texte%20à%20rechercher)

### Rechercher dans les titres des documents

Le paramètre __title__ permet d'effectuer une recherche textuelle dans le
titre des documents PDF. Cette recherche s'applique sur les PDF pour lesquels
la propriété `titre` est définie.

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__title__=__Texte à rechercher__](
    http://localhost/onegeo/api/profiles/pdf/search?title=Texte%20à%20rechercher)

### Filtrer les résultats

#### Par la date de publication des documents

Les paramètres __date_gte__ et __date_lte__ permettent de filtrer les résultats
d'une requête par la date de publication des documents. Les filtres s'applique
sur les PDF pour lesquels la propriété `date_seance` est définie.

Quelques exemples :

* Retourner tous les documents postérieurs à juin 2015 :

  [http://localhost/onegeo/api/profiles/__{pdf}__/search?__date_gte__=__201506__](
    http://localhost/onegeo/api/profiles/pdf/search?date_gte=201506)

* Retourner tous les documents antérieurs à juin 2016 :

  [http://localhost/onegeo/api/profiles/__{pdf}__/search?__date_gte__=__201506__&__date_lte__=__201606__](
    http://localhost/onegeo/api/profiles/pdf/search?date_gte=201506&date_lte=201606)

* Retourner tous les documents entre juin 2015 et juin 2016 :

  [http://localhost/onegeo/api/profiles/__{pdf}__/search?__date_gte__=__201506__&__date_lte__=__201606__](
    http://localhost/onegeo/api/profiles/pdf/search?date_gte=201506&date_lte=201606)

#### Par la source

La paramètre __source__ permet de filtrer les résultats par le nom de la source
des documents, c'est à dire le premier niveau d'arborescence dans le répertoire
de stockage PDF synchronisé avec la plateforme Onegeo.

Attention, ce paramètre est sensible à la casse.

```
.
├── source_0/
└── source_1/
```

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__source__=__source_0__](
    http://localhost/onegeo/api/profiles/pdf/search?source=nom_de_la_source)

#### Par la ressource

La paramètre __resource__ permet de filtrer les résultats par le nom de la
ressource, soit le deuxième niveau d'arborescence dans le répertoire de
stockage PDF synchronisé avec la plateforme Onegeo (le premier niveau étant
la __source__).

Attention, ce paramètre est sensible à la casse.

```
.
├── source_0/
|   ├── resource_0/
|   ├── resource_1/
|   └── resource_2/
└── source_1/
    ├── resource_3/
    └── resource_4/
```

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__resource__=__resource_3__](
    http://localhost/onegeo/api/profiles/pdf/search?resource=nom_de_la_ressource)

#### Par la commune

Le paramètre __city__ permet de filtrer les résultats d'une requête par
la commune. Le filtre s'applique sur les PDF pour lesquels la propriété
`communes` est définie.

Attention, ce paramètre est sensible à la casse.

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__city__=__Nom de la commune__](
    http://localhost/onegeo/api/profiles/pdf/search?commune=Nom%20de%20la%20commune)

#### Par le numéro de séance

Le paramètre __session_id__ permet de filtrer les résultats d'une requête par
le type de séance. Le filtre s'applique sur les PDF pour lesquels la propriété
`numero_seance` (de type `keyword`) est définie.

Attention, ce paramètre est sensible à la casse.

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__session_id__=__Numéro de la séance__](
    http://localhost/onegeo/api/profiles/pdf/search?commune=Numéro%20de%20la%20séance)

#### Par le type de séance

Le paramètre __session_type__ permet de filtrer les résultats d'une requête par
le type de séance. Le filtre s'applique sur les PDF pour lesquels la propriété
`type_seance` (de type `keyword`) est définie.

Attention, ce paramètre est sensible à la casse.

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__session_type__=__Type de la séance__](
    http://localhost/onegeo/api/profiles/pdf/search?commune=Type%20de%20la%20séance)

#### Trier les résultats

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__sort_by__=__date_seance__](
    http://localhost/onegeo/api/profiles/pdf/search?sort_by=date_seance)

Pour obtenir l'ordre décroissant, préfixez la valeur de champ par le signe _[_ __-__ _]_.

[http://localhost/onegeo/api/profiles/__{pdf}__/search?__sort_by__=__-date_seance__](
    http://localhost/onegeo/api/profiles/pdf/search?sort_by=-date_seance)
