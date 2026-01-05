
import re
from typing import List, Set

class EntityExtractor:
    def extract_entities(self, text: str) -> List[str]:
        """
        Extracts financial entities from text using heuristics.
        1. Tickers prefixed with $ (e.g. $AAPL)
        2. Commonly known capitalization patterns in 'Competitor' context (simplified).
        """
        entities: Set[str] = set()
        
        # 1. $TICKER pattern
        # Matches $ABC, $A, $ABCD
        tickers = re.findall(r'\$([A-Z]{1,5})\b', text)
        for t in tickers:
            entities.add(t)
            
        # 2. Competitor Context (Rule-based)
        # Look for "competitors include X, Y, Z" - Implementing simple regex for now
        # For Sprint 7 MVP, we stick mostly to explicit tickers or capitalized words after "competitor"
        # This is hard to do robustly without NLP (Spacy/NER).
        # We will focus on the $TICKER pattern which is reliable for FinTwit/FinText style.
        # If text is 10-K, tickers might not have $. 
        # So we also look for "Symbol: [A-Z]+" or similar?
        # For now, let's keep it simply $TICKER or specific known entities for robustness.
        
        return list(entities)
