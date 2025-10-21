"""PyST API integration service."""
import httpx
import os
import re
from typing import List, Optional
from app.models.schemas import PystConcept, ColumnMapping, MappingResult


class PystService:
    """Service for interacting with PyST ontology API."""
    
    def __init__(self):
        self.base_url = os.getenv("PYST_HOST", "https://vocab.sentier.dev/api/v1/").rstrip('/')
        self.api_key = os.getenv("PYST_AUTH_TOKEN", "")
        self.timeout = float(os.getenv("PYST_TIMEOUT", "30"))
        self.headers = {
            "Content-Type": "application/json",
        }
        # PyST uses "x-pyst-auth-token" header, not Bearer token
        if self.api_key:
            self.headers["x-pyst-auth-token"] = self.api_key
    
    def extract_search_term(self, column_name: str) -> str:
        """
        Extract the most meaningful search term from a column name.
        Takes the first word or the most significant word.
        
        Examples:
            "Patient ID" -> "Patient"
            "Blood_Pressure" -> "Blood"
            "temperature_celsius" -> "temperature"
        """
        # Remove special characters and split
        words = re.sub(r'[_\-\.]+', ' ', column_name).split()
        
        # Filter out common meaningless words
        stop_words = {'id', 'code', 'value', 'name', 'number', 'num', 'val', 'data'}
        
        for word in words:
            if word.lower() not in stop_words and len(word) > 2:
                return word
        
        # If all words are stop words, return the first one
        return words[0] if words else column_name
    
    async def search_concepts(self, query: str, language: str = "en") -> List[PystConcept]:
        """
        Search PyST ontology concepts using the suggest endpoint.
        
        Args:
            query: Search query string
            language: ISO 639-1 language code (en, de, es, fr, pt, it, da)
            
        Returns:
            List of matching PyST concepts
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                # Use PyST suggest endpoint: /concepts/suggest/
                url = f"{self.base_url}/concepts/suggest/"
                
                response = await client.get(
                    url,
                    params={"query": query, "language": language},
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                print(f"PyST API Request: {url}?query={query}&language={language}")
                print(f"PyST API Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"PyST API Response: Found {len(data) if isinstance(data, list) else 'unknown'} concepts")
                    
                    concepts = []
                    # PyST suggest returns a list of concepts directly
                    for item in data:
                        try:
                            # Map PyST response to our schema
                            # PyST returns: label, iri, score, etc.
                            concept = PystConcept(
                                id=item.get("iri", ""),
                                name=item.get("label", ""),
                                description=item.get("definition", ""),
                                category=item.get("scheme", ""),
                                uri=item.get("iri", "")
                            )
                            concepts.append(concept)
                            print(f"  - {concept.name} (IRI: {concept.uri})")
                        except Exception as e:
                            print(f"Error parsing concept: {e}, item: {item}")
                            continue
                    
                    return concepts
                else:
                    print(f"PyST API error: Status {response.status_code}")
                    print(f"Response: {response.text}")
                    return []
        except Exception as e:
            print(f"PyST API error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_concept_by_id(self, concept_iri: str) -> Optional[PystConcept]:
        """
        Get specific concept by IRI.
        
        Args:
            concept_iri: The concept IRI (full URI)
            
        Returns:
            PystConcept if found, None otherwise
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                # PyST uses /concepts/{iri} endpoint
                response = await client.get(
                    f"{self.base_url}/concepts/{concept_iri}",
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Map PyST concept details to our schema
                    return PystConcept(
                        id=data.get("iri", concept_iri),
                        name=data.get("label", ""),
                        description=data.get("http://www.w3.org/2004/02/skos/core#definition", ""),
                        category=data.get("scheme", ""),
                        uri=data.get("iri", concept_iri)
                    )
                return None
        except Exception as e:
            print(f"PyST API error getting concept: {e}")
            return None
    
    async def get_auto_mappings(self, columns: List[str]) -> MappingResult:
        """
        Get automatic mapping suggestions for Excel columns.
        
        Uses the first word of the column name for semantic matching.
        
        Args:
            columns: List of Excel column names
            
        Returns:
            MappingResult with suggested mappings
        """
        mappings = []
        unmapped_columns = []
        
        for column in columns:
            # Extract the most meaningful search term (usually first word)
            search_term = self.extract_search_term(column)
            
            print(f"Auto-mapping column '{column}' using search term '{search_term}'")
            
            # Search for concepts that match the search term
            concepts = await self.search_concepts(search_term)
            
            if concepts:
                # Calculate confidence based on name similarity
                best_match = concepts[0]
                
                # Simple confidence scoring based on string similarity
                column_lower = column.lower()
                concept_name_lower = best_match.name.lower()
                
                if search_term.lower() in concept_name_lower:
                    confidence = 0.90
                elif any(word in concept_name_lower for word in column_lower.split()):
                    confidence = 0.75
                else:
                    confidence = 0.60
                
                mappings.append(ColumnMapping(
                    excelColumn=column,
                    pystConcept=best_match,
                    confidence=confidence
                ))
                
                print(f"  → Mapped to '{best_match.name}' (confidence: {confidence})")
            else:
                unmapped_columns.append(column)
                mappings.append(ColumnMapping(
                    excelColumn=column,
                    pystConcept=None,
                    confidence=0.0
                ))
                
                print(f"  → No match found")
        
        return MappingResult(mappings=mappings, unmappedColumns=unmapped_columns)


# Singleton instance
pyst_service = PystService()
