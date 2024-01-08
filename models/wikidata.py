import logging
from pprint import pprint

from pydantic import BaseModel
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.datatypes import ExternalID as ExternalIdDatatype

# This config sets the URL for the Wikibase and tool.
import config

logger = logging.getLogger(__name__)


# class WikidataNamespaceLetters(Enum):
#     PROPERTY = "P"
#     ITEM = "Q"
#     LEXEME = "L"


class ExternalID(BaseModel):
    id: str  # external id
    property: str  # This is the property with type ExternalId


class Lexeme(BaseModel):
    id: str
    lemma: str
    lexical_category: str
    wbi: WikibaseIntegrator

    class Config:
        arbitrary_types_allowed = True

    def url(self):
        return f"{config.wd_prefix}{self.id}"

    def upload_foreign_id_to_wikidata(self, external_id: ExternalID = None):
        """Upload to enrich the wonderful Wikidata <3"""
        if external_id is None:
            raise Exception("Foreign id was None")
        if not self.id:
            raise ValueError("self.id was empty")
        print(f"Uploading {external_id.id} to {self.id}: {self.lemma}")
        statement = ExternalIdDatatype(
            prop_nr=external_id.property,
            value=external_id.id,
        )
        lexeme = self.wbi.lexeme.get(entity_id=self.id)
        lexeme.claims.add(claims=[statement])
        pprint(lexeme.get_json())
        input("press enter to upload")
        lexeme.write(
            summary=f"Added ODS identifier with [[Wikidata:Tools/LexODS|LexODS]]"
        )
        print(lexeme.get_entity_url())
        input("press enter to continue")
