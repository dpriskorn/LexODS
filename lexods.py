#!/usr/bin/env python3
# Licensed under GPLv3+ i.e. GPL version 3 or later.
import logging
from csv import reader
from typing import List, Dict

from pydantic import BaseModel
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_helpers import execute_sparql_query
from wikibaseintegrator.wbi_login import Login

import config
from models import wikidata, ods_entry
from models.ods_entry import Entry
from models.wikidata import Lexeme

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)


class OdsMatcher(BaseModel):
    ods_lemma_list: List[str] = list()
    ods_data: Dict[int, Entry] = dict()
    wbi: WikibaseIntegrator = WikibaseIntegrator(
        login=Login(user=config.username, password=config.password)
    )

    class Config:
        arbitrary_types_allowed = True

    def load_ods_into_memory(self) -> None:
        # load all saab words into a list that can be searched
        # load all saab ids into a list we can lookup in using the index.
        # the two lists above have the same index.
        # load all ODS lines into a dictionary with count as key and list in the value
        print("Loading ODS into memory")
        # open file in read mode
        with open("ods_2024-01-07.csv", "r") as read_obj:
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
                    id=id, lexical_category_qid=str(lexical_category), lemma=str(lemma)
                )
                self.ods_data[count] = entry
                self.ods_lemma_list.append(lemma)
                count += 1
        print(
            f"loaded {count} ODS lines into dictionary with length {len(self.ods_data)}"
        )
        print(
            f"loaded {count} ODS lines into list with length {len(self.ods_lemma_list)}"
        )

    @staticmethod
    def categories_match(lexeme: wikidata.Lexeme, ods_entry: ods_entry.Entry) -> bool:
        if ods_entry.lexical_category_qid is not None:
            if lexeme.lexical_category == ods_entry.lexical_category_qid:
                return True
            else:
                return False
        else:
            raise Exception("ODS entry was None")

    def process_lexemes(
        self, lexeme_lemma_list: List = None, lexemes_data: Dict = None
    ):
        if lexeme_lemma_list is None or lexemes_data is None:
            logger.exception("Did not get what we need")
        lexemes_count = len(lexeme_lemma_list)
        # go through all lexemes missing ODS identifier
        match_count = 0
        processed_count = 0
        skipped_multiple_matches = 0
        if config.count_only:
            print("Counting all matches that can be uploaded")
        for lexeme in lexeme_lemma_list:
            if processed_count > 0 and processed_count % 10 == 0:
                print(
                    f"Processed {processed_count}/"
                    f"{lexemes_count} ({round(processed_count * 100 / lexemes_count)}%)\n"
                    f"Found {match_count} matches "
                    f"out of which {skipped_multiple_matches} "
                    f"was skipped because they had multiple entries in ODS "
                    f"with the same lexical category."
                )
            lexeme: wikidata.Lexeme = lexemes_data[lexeme]
            if not config.count_only:
                logging.info(
                    f"Working on {lexeme.id}: {lexeme.lemma}, lexcat: {lexeme.lexical_category}"
                )
            value_count = 0
            matching_ods_indexes = []
            if lexeme.lemma in self.ods_lemma_list:
                logger.info("Found lemma in ods_lemma_list")
                # exit()
                # Count number of hits
                for count, lemma in enumerate(self.ods_lemma_list):
                    if lemma == lexeme.lemma:
                        # print(count, value)
                        matching_ods_indexes.append(count)
                        value_count += 1
                if value_count > 1:
                    if not config.count_only:
                        logger.debug(f"Found more than 1 matching lemma = complex")
                        adj_count = 0
                        noun_count = 0
                        verb_count = 0
                        for index in matching_ods_indexes:
                            entry = self.ods_data[index]
                            if entry.is_noun:
                                logging.debug(
                                    f"Detected noun: {entry.lexical_category_qid}"
                                )
                                noun_count += 1
                            if entry.is_verb:
                                logging.debug(
                                    f"Detected verb: {entry.lexical_category_qid}"
                                )
                                verb_count += 1
                            if entry.is_adjective:
                                logging.debug(
                                    f"Detected adjective: {entry.lexical_category_qid}"
                                )
                                adj_count += 1
                        logger.info(
                            f"Counts: noun:{noun_count}, verb:{verb_count}, adj:{adj_count}"
                        )
                        # exit()
                        for index in matching_ods_indexes:
                            # pprint(self.ods_data[index])
                            # exit()
                            entry = self.ods_data[index]
                            logging.debug(
                                f"index {index} "
                                f"lemma: '{entry.lemma}' "
                                f"lexcat: '{entry.lexical_category_qid}' "
                                # f"number {entry.number}, "
                                f"see {entry.url()}"
                            )
                            if self.categories_match(lexeme=lexeme, ods_entry=entry):
                                match_count += 1
                                if not config.count_only:
                                    logging.info("Categories match")
                                    if entry.is_noun:
                                        if noun_count > 1:
                                            logging.info(
                                                "More that one noun found "
                                                "for this lemma in ODS. Skipping"
                                            )
                                            skipped_multiple_matches += 1
                                            continue
                                    if entry.is_verb:
                                        if verb_count > 1:
                                            logging.info(
                                                "More that one verb found "
                                                "for this lemma in ODS. Skipping"
                                            )
                                            skipped_multiple_matches += 1
                                            continue
                                    if entry.is_adjective:
                                        if adj_count > 1:
                                            logging.info(
                                                f"More that one adj found "
                                                f"for this lemma in ODS. Skipping"
                                            )
                                            skipped_multiple_matches += 1
                                            continue
                                    self.check_and_upload(lexeme=lexeme, entry=entry)
                            else:
                                logger.debug("Categories did not match")
                elif value_count == 1:
                    # Only 1 search result in the ODS wordlist so pick it
                    entry = self.ods_data[matching_ods_indexes[0]]
                    logger.debug(f"Only one matching lemma, see {entry.url()}")
                    if self.categories_match(lexeme=lexeme, ods_entry=entry):
                        match_count += 1
                        if not config.count_only:
                            logging.info("Categories match")
                            self.check_and_upload(lexeme=lexeme, entry=entry)
                    else:
                        logger.debug("Categories did not match")
                print("")
                from time import sleep

                sleep(5)
            else:
                if not config.count_only:
                    logging.debug(f"{lexeme.lemma} not found in ODS wordlist")
            processed_count += 1
            # exit()

    def check_and_upload(self, lexeme, entry):
        if (
            self.number_of_lexemes_with_identical_lemma_and_lexcat(
                lemma=lexeme.lemma, lexcat=entry.lexical_category_qid
            )
            == 1
        ):
            foreign_id = wikidata.ExternalID(
                id=str(entry.id),
                property="P9962",
            )
            lexeme.upload_foreign_id_to_wikidata(external_id=foreign_id)
        else:
            logger.info(
                "Skipping lexeme. We don't support matching on lexemes where "
                "multiple exists with identical lemma and lexical category"
            )

    def start(self):
        if not config.count_only:
            print("Logging in with Wikibase Integrator")
            # config.login_instance = wbi_login.Login(
            #     user=config.username, pwd=config.password
            # )
        lexemes_list, lexemes_data = self.fetch_lexemes(
            property="P9962", language_item_id="Q9035"
        )
        self.load_ods_into_memory()
        self.process_lexemes(lexeme_lemma_list=lexemes_list, lexemes_data=lexemes_data)

    def fetch_lexemes(self, property: str = None, language_item_id: str = None):
        """Fetch all lexemes to work on"""
        if language_item_id is None:
            raise Exception("Got no language")
        if property is None:
            raise Exception("Got no property")
        # dictionary with word as key and list in the value
        # list[0] = lid
        # list[1] = category Qid
        print("Fetching all lexemes")
        lexemes_data = {}
        lexeme_lemma_list = []
        for i in range(0, 30000, 10000):
            print(i)
            results = execute_sparql_query(
                f"""
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
            """
            )
            if len(results) == 0:
                print("No lexeme found")
            else:
                for result in results["results"]["bindings"]:
                    # print(result)
                    # *************************
                    # Handle result and upload
                    # *************************
                    lemma = result["lemma"]["value"]
                    lid = result["lexemeId"]["value"].replace(config.wd_prefix, "")
                    lexical_category = result["category"]["value"].replace(
                        config.wd_prefix, ""
                    )
                    lexeme = Lexeme(
                        id=lid,
                        lemma=lemma,
                        lexical_category=lexical_category,
                        wbi=self.wbi,
                    )
                    # Populate the dictionary with lexeme objects
                    lexemes_data[lemma] = lexeme
                    # Add lemma to list (used for optimization)
                    lexeme_lemma_list.append(lemma)
        lexemes_count = len(lexeme_lemma_list)
        print(f"{lexemes_count} fetched")
        # exit(0)
        return lexeme_lemma_list, lexemes_data

    @staticmethod
    def number_of_lexemes_with_identical_lemma_and_lexcat(lemma, lexcat) -> int:
        query = f"""
            SELECT (COUNT(?lexeme) as ?count) WHERE {{
                ?lexeme dct:language wd:Q9035;
                        wikibase:lemma "{lemma}"@da;
                        wikibase:lexicalCategory wd:{lexcat}.
            }}
        """
        data = execute_sparql_query(query)
        count = int(data["results"]["bindings"][0]["count"]["value"])
        logger.info(f"Found {count} lexemes with the same lemma and category in WD")
        return count


om = OdsMatcher()
om.start()
