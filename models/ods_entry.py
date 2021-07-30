import json
import logging
from typing import List


class Entry():
    lemma: str
    # This id is found in the list we scrape
    id: str
    # Entry id is unique and only found on the page of the entry, not in the list we scrape
    entry_id: int
    lexical_category: str
    # each definition also has an id but we don't support that yet
    # definitions: List

    def __init__(self,
                 id: int = None,
                 lemma: str = None,
                 lexical_category: str = None):
        self.id = id
        self.lemma = lemma
        self.lexical_category = self.__find_lexical_category_qid(lexical_category)

    def __find_lexical_category_qid(self, string):
        logger = logging.getLogger(__name__)
        if (string == "sb." or string == "subst."
                or string == "symbol" or string == "pl." or string == "fork."):
            return "Q1084"  # noun
        elif string == "vb." or string == "v.":
            return "Q24905"  # verb
        elif string == "adj." or string == "part.adj.":
            return "Q34698"  # adjective
        elif string == "suffix" or string == "præfiks":
            return "Q62155"  # affix
        elif string == "udråbsord" or string == "interj.":
            return "Q83034"  # interj
        elif string == "præp.":
            return "Q4833830"  # preposition
        elif string == "adv.":
            return "Q380057"  # adverb
        elif string == "propr.":
            return "Q147276"  # proper noun
        elif string == "num.":
            return "Q63116"  # numeral
        else:
            logger.error(f"Lexical category {string} not recognized, see {self.url()}")
            exit(0)

    def json(self):
        return json.dumps(dict(
            id=self.id,
            l=self.lemma,
            lc=self.lexical_category
        ))

    def csv(self):
        return f"{self.id},{self.lemma},{self.lexical_category}\n"

    def url(self):
        return f"https://ordnet.dk/ods/ordbog?entry_id={self.id}&query=wd"
