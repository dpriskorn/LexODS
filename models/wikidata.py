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


class ForeignID:
    id: str
    property: str  # This is the property with type ExternalId
    source_item_id: str  # This is the Q-item for the source

    def __init__(self,
                 id: str = None,
                 property: str = None,
                 source_item_id: str = None):
        self.id = id
        self.property = EntityID(property).to_string()
        self.source_item_id = EntityID(source_item_id).to_string()


class Lexeme:
    id: str
    lemma: str
    lexical_category: str

    def __init__(self,
                 id: str = None,
                 lemma: str = None,
                 lexical_category: str = None):
        self.id = EntityID(id).to_string()
        self.lemma = lemma
        self.lexical_category = lexical_category

    def url(self):
        return f"{config.wd_prefix}{self.id}"

    def upload_foreign_id_to_wikidata(self,
                                      foreign_id: ForeignID = None):
        """Upload to enrich the wonderful Wikidata <3"""
        logger = logging.getLogger(__name__)
        if foreign_id is None:
            raise Exception("Foreign id was None")
        print(f"Uploading {foreign_id.id} to {self.id}: {self.lemma}")
        statement = wbi_core.ExternalID(
            prop_nr=foreign_id.property,
            value=foreign_id.id,
        )
        described_by_source = wbi_core.ItemID(
            prop_nr="P1343",  # stated in
            value=foreign_id.source_item_id
        )
        item = wbi_core.ItemEngine(
            data=[statement,
                  described_by_source],
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
