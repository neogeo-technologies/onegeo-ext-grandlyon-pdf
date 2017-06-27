#### Tableau de migration depuis l'ancien service

| Paramètre    | Ancien paramètre                                              |
|------------- | ------------------------------------------------------------- |
| city         | Remplace le paramètre __communes__                            |
| date_gte     | Concaténation des paramètres __anneeD__ + __moisD__           |
| date_lte     | Concaténation des paramètres __anneeF__ + __moisF__           |
| from         | Remplace le paramètre __debut__                               |
| group_by     |                                                               |
| resource (2) | Peut remplacer le paramètre __selCollection__ (Cf. remarques) |
| size         |                                                               |
| sort_by (3)  | Concaténation des paramètres __ordtri__ et __sujtri__         |
| source (1)   | Peut remplacer le paramètre __selCollection__ (Cf. remarques) |
| suggest      | Pas d'équivalent                                              |
| suggest_mode | Pas d'équivalent                                              |
| text         | Remplace le paramètre __motscles__                            |
| title        | Remplace le paramètre __titre__                               |


##### Remarques :

(1) Le paramètre __source__ prend comme valeur le nom des répertoires racines
dans le dépôt PDF (par exemple si les PDF sont regroupés par types de documents
_RAAD_, _LYVIA_, etc.).

(2) Le paramètre __resource__ prend comme valeur le nom des premiers niveaux de
sous-répertoire dans l'arborescence d'une __source__. Si par exemple les PDF
sont classés par type de séance au sein d'une même __source__ alors __resource__
correspond au type de séance.

(3) Le paramètre __sort_by__ permet de trier les résultats d'une requête sur un
attribut donné. Ce paramètre fonctionne avec les attributs configurés dans le
profil d'indexation de Onegeo.

Le mode ascendant est le mode par défaut, il n'y a rien à paramétrer.
Pour inverser le tri, il suffit de préfixer le nom de l'attribut par le
caractère négatif, par exemple `..&sort_by=-date_seance` (__date_seance__ doit
bien évidemment être un champ valide).

##### Paramètre(s) n'étant plus supporté(s)

L'ancien paramètre __collectivite__ n'est pas supporté dans ce nouveau service
mais peut être remplacé par un filtre sur la date (__date_gte__).
