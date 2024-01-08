import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Entry(BaseModel):
    lemma: str
    # This id is found in the list we scrape
    id: int
    # # Entry id is unique and only found on the page of the entry, not in the list we scrape
    # entry_id: int
    lexical_category_qid: str = ""
    lexical_category: str = ""
    # each definition also has an id but we don't support that yet
    # definitions: List

    @property
    def fixed_lemma(self):
        lemma = self.lemma.replace("aa", "å")
        # Lowercase all except proper nouns to easier match the lemmas with Wikidata
        if self.lexical_category_qid != "Q147276":
            lemma = lemma.lower()
        return lemma

    # def __init__(self, id: int = None, lemma: str = None, lexical_category: str = None):
    #     self.id = id
    #     self.lexical_category = self.__find_lexical_category_qid(lexical_category)
    #     # Lowercase all except proper nouns to easier match the lemmas with Wikidata
    #     if self.lexical_category != "Q147276":
    #         self.lemma = lemma.lower()
    #     else:
    #         self.lemma = lemma
    #     if "aa" in self.lemma:
    #         self.lemma = self.lemma.replace("aa", "å")

    @property
    def is_noun(self):
        return bool(self.lexical_category_qid == "Q1084")

    @property
    def is_adjective(self):
        return bool(self.lexical_category_qid == "Q34698")

    @property
    def is_verb(self):
        return bool(self.lexical_category_qid == "Q24905")

    def __parse_lexical_category(self):
        """get the corresponding qid and store it"""
        if (
            self.lexical_category == "sb."
            or self.lexical_category == "subst."
            or self.lexical_category == "symbol"
            or self.lexical_category == "pl."
            or self.lexical_category == "fork."
        ):
            self.lexical_category_qid = "Q1084"  # noun
        elif self.lexical_category == "vb." or self.lexical_category == "v.":
            self.lexical_category_qid = "Q24905"  # verb
        elif (
            self.lexical_category == "adj."
            or self.lexical_category == "part.adj."
            or self.lexical_category == "part. adj."
        ):
            self.lexical_category_qid = "Q34698"  # adjective
        elif (
            self.lexical_category == "suffix"
            or self.lexical_category == "præfiks"
            or self.lexical_category == "i ssgr."
            or self.lexical_category == "suffiks."
        ):
            self.lexical_category_qid = "Q62155"  # affix
        elif self.lexical_category == "udråbsord" or self.lexical_category == "interj.":
            self.lexical_category_qid = "Q83034"  # interj
        elif self.lexical_category == "præp.":
            self.lexical_category_qid = "Q4833830"  # preposition
        elif self.lexical_category == "adv.":
            self.lexical_category_qid = "Q380057"  # adverb
        elif self.lexical_category == "propr.":
            self.lexical_category_qid = "Q147276"  # proper noun
        elif self.lexical_category == "num.":
            self.lexical_category_qid = "Q63116"  # numeral
        elif self.lexical_category == "konj.":
            self.lexical_category_qid = "Q36484"  # conjunction
        elif self.lexical_category == "pron.":
            self.lexical_category_qid = "Q36224"  # pronoun
        elif self.lexical_category is None:
            logger.error(f"No lexical category found for {self.url()}")
        # elif self.lexical_category == "subst. ell. (i bet. 1) en." or self.lexical_category == "interj., adj." or self.lexical_category == "adv. og adj.":
        #     return None
        else:
            logger.error(
                f"Lexical category {self.lexical_category} not recognized, see {self.url()}"
            )

    # def json(self):
    #     return json.dumps(dict(id=self.id, l=self.lemma, lc=self.lexical_category_qid))

    def csv(self):
        return f"{self.id},{self.fixed_lemma},{self.lexical_category_qid}\n"

    def url(self):
        return f"https://ordnet.dk/ods/ordbog?entry_id={self.id}&query=wd"
