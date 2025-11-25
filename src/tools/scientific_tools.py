"""Scientific fact-checking tools using real APIs.

This module implements tools for retrieving and assessing scientific literature
using the PubMed/Entrez API.
"""

import os
from typing import List, Dict, Any
from Bio import Entrez
from dotenv import load_dotenv

load_dotenv()

# Set email for Entrez (required by NCBI)
Entrez.email = os.getenv("PUBMED_EMAIL", "user@example.com")


def pubmed_literature_retriever(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Search PubMed for scientific literature related to the query.
    
    Args:
        query: Search query for scientific literature
        max_results: Maximum number of results to return
        
    Returns:
        Dictionary with search results including PMIDs, titles, abstracts, etc.
    """
    try:
        # Search PubMed
        search_handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results,
            sort="relevance"
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()
        
        pmids = search_results["IdList"]
        
        if not pmids:
            return {
                "source": "PubMed",
                "query": query,
                "results": [],
                "count": 0
            }
        
        # Fetch details for the papers
        fetch_handle = Entrez.efetch(
            db="pubmed",
            id=pmids,
            rettype="medline",
            retmode="xml"
        )
        papers = Entrez.read(fetch_handle)
        fetch_handle.close()
        
        # Parse results
        results = []
        for paper in papers['PubmedArticle']:
            article = paper['MedlineCitation']['Article']
            
            # Extract title
            title = article.get('ArticleTitle', 'No title')
            
            # Extract abstract
            abstract_parts = article.get('Abstract', {}).get('AbstractText', [])
            if abstract_parts:
                abstract = ' '.join([str(part) for part in abstract_parts])
            else:
                abstract = "No abstract available"
            
            # Extract journal and year
            journal = article.get('Journal', {}).get('Title', 'Unknown journal')
            pub_date = article.get('Journal', {}).get('JournalIssue', {}).get('PubDate', {})
            year = pub_date.get('Year', 'Unknown year')
            
            # Extract PMID
            pmid = str(paper['MedlineCitation']['PMID'])
            
            results.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "journal": journal,
                "year": year,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
        
        return {
            "source": "PubMed",
            "query": query,
            "results": results,
            "count": len(results),
            "confidence": 0.9  # High confidence for peer-reviewed sources
        }
        
    except Exception as e:
        print(f"Error retrieving PubMed data: {e}")
        return {
            "source": "PubMed",
            "query": query,
            "results": [],
            "count": 0,
            "error": str(e)
        }


def study_quality_assessor(pmid: str, study_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess the quality of a scientific study based on metadata.
    
    Args:
        pmid: PubMed ID
        study_metadata: Metadata about the study (title, abstract, year, etc.)
        
    Returns:
        Dictionary with quality score and assessment details
    """
    quality_score = 0.5  # Base score
    study_type = "observational"  # Default
    factors = []
    
    # Check publication year (recent = better)
    try:
        year = int(study_metadata.get("year", "2000"))
        if year >= 2020:
            quality_score += 0.2
            factors.append("Recent publication (2020+)")
        elif year >= 2015:
            quality_score += 0.1
            factors.append("Moderately recent (2015+)")
    except (ValueError, TypeError):
        pass
    
    # Check for study type keywords in title/abstract
    text = (study_metadata.get("title", "") + " " + 
            study_metadata.get("abstract", "")).lower()
    
    if any(keyword in text for keyword in ["randomized controlled trial", "rct", "double-blind"]):
        quality_score += 0.3
        study_type = "RCT"
        factors.append("Randomized Controlled Trial (highest quality)")
    elif any(keyword in text for keyword in ["meta-analysis", "systematic review"]):
        quality_score += 0.25
        study_type = "meta-analysis"
        factors.append("Meta-analysis or Systematic Review")
    elif any(keyword in text for keyword in ["cohort study", "prospective"]):
        quality_score += 0.15
        study_type = "cohort"
        factors.append("Cohort study")
    elif any(keyword in text for keyword in ["case-control"]):
        quality_score += 0.1
        study_type = "case-control"
        factors.append("Case-control study")
    
    # Cap at 1.0
    quality_score = min(quality_score, 1.0)
    
    # Convert to confidence (0.0-1.0)
    confidence = quality_score
    
    return {
        "pmid": pmid,
        "quality_score": quality_score,
        "study_type": study_type,
        "confidence": confidence,
        "assessment_factors": factors
    }


if __name__ == "__main__":
    # Test the tools
    print("Testing PubMed Literature Retriever...")
    results = pubmed_literature_retriever("cancer india best", max_results=3)
    
    print(f"\nFound {results['count']} papers:")
    for paper in results['results']:
        print(f"\n- {paper['title']}")
        print(f"  Journal: {paper['journal']} ({paper['year']})")
        print(f"  PMID: {paper['pmid']}")
        print(f"  Abstract: {paper['abstract'][:200]}...")
        
        # Assess quality
        quality = study_quality_assessor(paper['pmid'], paper)
        print(f"  Quality: {quality['quality_score']:.2f} ({quality['study_type']})")
