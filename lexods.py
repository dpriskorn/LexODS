#!/usr/bin/env python3
# Licensed under GPLv3+ i.e. GPL version 3 or later.
import logging
from csv import reader
from typing import List, Dict

from wikibaseintegrator import wbi_core, wbi_login

import config
from models import wikidata, ods_entry

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def upload_to_wikidata(lexeme: wikidata.Lexeme = None,
                       entry: ods_entry.Entry = None):
    """Upload to enrich the wonderfull Wikidata <3"""
    if lexeme is None or entry is None:
        raise ValueError("Did not get the arguments needed")
    print(f"Uploading id to {lexeme.id}: {lexeme.lemma}")
    # TODO if numbered
    # - fetch lexeme using wbi
    # - present to user
    # - ask user which if one matches
    print(f"Adding {entry.id}")
    ods_statement = wbi_core.ExternalID(
        prop_nr="P8478",
        value=entry.id,
    )
    described_by_source = wbi_core.ItemID(
        prop_nr="P1343",
        value="Q1935308"
    )
    item = wbi_core.ItemEngine(
        data=[ods_statement,
              described_by_source],
        # append_value="P8478",
        item_id=lexeme.id
    )
    # debug WBI error
    # print(item.get_json_representation())
    result = item.write(
        config.login_instance,
        edit_summary="Added ODS identifier with [[Wikidata:Tools/LexODS]]"
    )
    # if config.debug_json:
    # logging.debug(f"result from WBI:{result}")
    print(lexeme.url())
    # exit(0)


def fetch_all_lexemes_without_ods_id():
    """download all swedish lexemes via sparql (~23000 as of 2021-04-05)"""
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
              ?lexemeId dct:language wd:Q9035;
                        wikibase:lemma ?lemma;
                        wikibase:lexicalCategory ?category.
              MINUS{{
              # FIXME
                ?lexemeId wdt:P8478 [].
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
                lexeme = wikidata.Lexeme(
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


def load_ods_into_memory():
    # load all saab words into a list that can be searched
    # load all saab ids into a list we can lookup in using the index.
    # the two lists above have the same index.
    # load all ODS lines into a dictionary with count as key and list in the value
    print("Loading ODS into memory")
    ods_lemma_list = []
    ods_data = {}
    # open file in read mode
    with open('ods_2021-07-30.csv', 'r') as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(read_obj)
        count = 0
        # Iterate over each row in the csv using reader object
        for row in csv_reader:
            # row variable is a list that represents a row in csv
            id = int(row[0])
            lemma = row[1]
            lexical_category = row[2]
            # Create object
            entry = ods_entry.Entry(
                id=id,
                lexical_category=lexical_category,
                lemma=lemma
            )
            ods_data[count] = entry
            ods_lemma_list.append(lemma)
            count += 1
    print(f"loaded {count} ODS lines into dictionary with length {len(ods_data)}")
    print(f"loaded {count} ODS lines into list with length {len(ods_lemma_list)}")
    # exit(0)
    return ods_lemma_list, ods_data


def check_matching_category(lexeme: wikidata.Lexeme,
                            ods_entry: ods_entry.Entry):
    if ods_entry.lexical_category is not None:
        if lexeme.lexical_category == ods_entry.lexical_category:
            return True
        else:
            return False
    else:
        return False


def process_lexemes(lexeme_lemma_list: List = None,
                    lexemes_data: Dict = None,
                    ods_lemma_list: List = None,
                    ods_data: Dict = None):
    if (
        lexeme_lemma_list is None or
        lexemes_data is None or
        ods_lemma_list is None or
        ods_data is None
    ):
        logger.exception("Did not get what we need")
    lexemes_count = len(lexeme_lemma_list)
    # go through all lexemes missing ODS identifier
    match_count = 0
    processed_count = 0
    skipped_multiple_matches = 0
    if config.count_only:
        print("Counting all matches that can be uploaded")
    for lexeme in lexeme_lemma_list:
        if processed_count > 0 and processed_count % 1000 == 0:
            print(f"Processed {processed_count} lexemes out of "
                  f"{lexemes_count} ({round(processed_count * 100 / lexemes_count)}%)")
        lexeme: wikidata.Lexeme = lexemes_data[lexeme]
        if not config.count_only:
            logging.info(f"Working on {lexeme.id}: {lexeme.lemma} {lexeme.lexical_category}")
        value_count = 0
        matching_ods_indexes = []
        if lexeme.lemma in ods_lemma_list:
            # Count number of hits
            for count, lemma in enumerate(ods_lemma_list):
                if lemma == lexeme.lemma:
                    # print(count, value)
                    matching_ods_indexes.append(count)
                    value_count += 1
            if value_count > 1:
                if not config.count_only:
                    logger.debug(f"Found more than 1 matching lemma = complex")
                    adj_count = 0
                    subst_count = 0
                    verb_count = 0
                    adjective_regex = "adj"
                    for index in matching_ods_indexes:
                        entry = ods_data[index]
                        if "subst" in entry.lexical_category:
                            logging.debug(f"Detected noun: {entry.lexical_category}")
                            subst_count += 1
                        if "verb" in entry.lexical_category:
                            logging.debug(f"Detected verb: {entry.lexical_category}")
                            verb_count += 1
                        if "adj" in entry.lexical_category:
                            logging.debug(f"Detected adjective: {entry.lexical_category}")
                            adj_count += 1
                    for index in matching_ods_indexes:
                        entry = ods_data[index]
                        logging.debug(f"index {index} lemma: {entry.lemma} {entry.lexical_category} "
                              f"number {entry.number}, see {entry.url()}")
                        result: bool = check_matching_category(lexeme=lexeme,
                                                               ods_entry=entry)
                        if result:
                            logging.info("Categories match")
                            match_count += 1
                            if not config.count_only:
                                if entry.lexical_category == "subst":
                                    if subst_count > 1:
                                        logging.info("More that one noun found. Skipping")
                                        skipped_multiple_matches += 1
                                        continue
                                if entry.lexical_category == "verb":
                                    if verb_count > 1:
                                        logging.info("More that one verb found. Skipping")
                                        skipped_multiple_matches += 1
                                        continue
                                if entry.lexical_category == "adj":
                                    if adj_count > 1:
                                        logging.info("More that one adj found. Skipping")
                                        skipped_multiple_matches += 1
                                        continue
                                # TODO scrape entry definitions from ODS and let the user decide
                                # whether any match the senses of the lexeme if any
                                upload_to_wikidata(lexeme=lexeme, entry=entry)
            elif value_count == 1:
                # Only 1 search result in the ODS wordlist so pick it
                entry = ods_data[matching_ods_indexes[0]]
                logger.debug(f"Only 1 matching lemma, see {entry.url()}")
                result = check_matching_category(lexeme=lexeme,
                                                 ods_entry=entry)
                if result:
                    match_count += 1
                    if not config.count_only:
                        upload_to_wikidata(lexeme=lexeme, entry=entry)
        else:
            if not config.count_only:
                logging.debug(f"{lexeme.lemma} not found in ODS wordlist")
        processed_count += 1
    print(f"Processed {processed_count} lexemes. "
          f"Found {match_count} matches "
          f"out of which {skipped_multiple_matches} "
          f"was skipped because they had multiple entries "
          f"with the same lexical category.")


def main():
    if not config.count_only:
        print("Logging in with Wikibase Integrator")
        config.login_instance = wbi_login.Login(
            user=config.username, pwd=config.password
        )
    lexemes_list, lexemes_data = fetch_all_lexemes_without_ods_id()
    ods_list, ods_data = load_ods_into_memory()
    process_lexemes(lexeme_lemma_list=lexemes_list, lexemes_data=lexemes_data, ods_lemma_list=ods_list,
                    ods_data=ods_data)


if __name__ == "__main__":
    main()
