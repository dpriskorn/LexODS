from wikibaseintegrator import wbi_core

import config
from models.wikidata import Lexeme


def fetch_lexemes(property: str = None,
                  language_item_id: str = None):
    """Fetch all lexemes to work on"""
    if language_item_id is None:
        raise Exception("Got no language")
    if property is None:
        raise Exception("Got no property")
    #dictionary with word as key and list in the value
    #list[0] = lid
    #list[1] = category Qid
    print("Fetching all lexemes")
    lexemes_data = {}
    lexeme_lemma_list = []
    for i in range(0,30000,10000):
        print(i)
        results = wbi_core.ItemEngine.execute_sparql_query(f"""
                select ?lexemeId ?lemma ?category
            WHERE {{
              #hint:Query hint:optimizer "None".
              ?lexemeId dct:language wd:{language_item_id};
                        wikibase:lemma ?lemma;
                        wikibase:lexicalCategory ?category.
              MINUS{{
                ?lexemeId wdt:{property} [].
              }}
            }}
    limit 10000
    offset {i}
        """)
        if len(results) == 0:
            print("No lexeme found")
        else:
            for result in results["results"]["bindings"]:
                #print(result)
                #*************************
                # Handle result and upload
                #*************************
                lemma = result["lemma"]["value"]
                lid = result["lexemeId"]["value"].replace(config.wd_prefix, "")
                lexical_category = result["category"]["value"].replace(config.wd_prefix, "")
                lexeme = Lexeme(
                    id=lid,
                    lemma=lemma,
                    lexical_category=lexical_category
                )
                # Populate the dictionary with lexeme objects
                lexemes_data[lemma] = lexeme
                # Add lemma to list (used for optimization)
                lexeme_lemma_list.append(lemma)
    lexemes_count = len(lexeme_lemma_list)
    print(f"{lexemes_count} fetched")
    # exit(0)
    return lexeme_lemma_list, lexemes_data


