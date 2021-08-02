import logging
from enum import Enum

from wikibaseintegrator import wbi_core

# This config sets the URL for the Wikibase and tool.
import config


class WikidataNamespaceLetters(Enum):
    PROPERTY = "P"
    ITEM = "Q"
    LEXEME = "L"


class EntityID:
    letter: WikidataNamespaceLetters
    number: int

    def __init__(self,
                 entity_id: str = None):
        if entity_id is not None:
            if len(entity_id) > 1:
                self.letter = WikidataNamespaceLetters[entity_id[0]]
                self.number = int(entity_id[1:])
            else:
                raise Exception("Entity ID was too short.")
        else:
            raise Exception("Entity ID was None")

    def to_string(self):
        return f"{self.letter}{self.number}"


class Lexeme:
    id: str
    lemma: str
    lexical_category: str
    foreign_id: str
    property: str
    foreign_source_id: str

    def __init__(self,
                 id: str = None,
                 lemma: str = None,
                 lexical_category: str = None,
                 foreign_id: str = None,
                 property: str = None,
                 foreign_source_id: str = None):
        self.id = EntityID(id).to_string()
        self.lemma = lemma
        self.lexical_category = lexical_category
        self.foreign_id = foreign_id
        self.property = EntityID(property).to_string()
        self.foreign_source_id = EntityID(foreign_source_id).to_string()

    def url(self):
        return f"{config.wd_prefix}{self.id}"

    def upload_foreign_id_to_wikidata(self,):
        """Upload to enrich the wonderfull Wikidata <3"""
        logger = logging.getLogger(__name__)
        print(f"Uploading {self.foreign_id} to {self.id}: {self.lemma}")
        statement = wbi_core.ExternalID(
            prop_nr="P8478",
            value=self.foreign_id,
        )
        described_by_source = wbi_core.ItemID(
            prop_nr=self.property,
            value=self.foreign_source_id
        )
        item = wbi_core.ItemEngine(
            data=[statement,
                  described_by_source],
            # append_value="P8478",
            item_id=self.id
        )
        # debug WBI error
        # print(item.get_json_representation())
        result = item.write(
            config.login_instance,
            edit_summary=f"Added foreign identifier with [[{config.tool_url}]]"
        )
        logger.debug(f"result from WBI:{result}")
        print(self.url())
        # exit(0)
