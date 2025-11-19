"""Core workflow nodes for the Deep Research Framework.

This module implements the four main nodes of the research workflow:
- Planner: Decomposes queries into sub-questions
- Retrieval: Searches and scrapes content
- Reflection: Evaluates research completeness
- Synthesis: Generates final cited report

All nodes are tool-agnostic and request tools from the registry.
"""

import logging
from typing import Dict, Any

from core.state import ResearchState, log_tool_success, log_tool_failure
from registry.tool_registry import ToolRegistry
from registry.base_tool import ModelType
from models.tool_schemas import CitedReport

logger = logging.getLogger(__name__)


def planner_node(state: ResearchState, registry: ToolRegistry) -> ResearchState:
    """
    Planner node: Decomposes research query into sub-questions.
    
    Requests a fast LLM from the registry and generates 3-5 focused
    sub-questions that will guide the research process.
    
    Args:
        state: Current research state
        registry: Tool registry for accessing LLM
    
    Returns:
        Updated state with research_plan populated
    
    Requirements: 4.1, 5.3, 11.1
    """
    logger.info(f"Planner node: Processing query '{state['original_query']}'")
    
    try:
        # Request fast LLM from registry
        llm_tool = registry.get_tool("llm")
        
        if not llm_tool:
            logger.error("No LLM tool available in registry")
            log_tool_failure(
                state,
                node="planner",
                tool_category="llm",
                tool_name="unknown",
                error_msg="No LLM tool registered"
            )
            state["research_plan"] = []
            return state
        
        # Generate prompt for query decomposition
        prompt = f"""You are a research planning assistant. Break down the following research query into 3-5 focused sub-questions that will help gather comprehensive information.

Research Query: {state['original_query']}

Generate 3-5 specific sub-questions that:
1. Cover different aspects of the main query
2. Are specific and answerable through web search
3. Build toward a comprehensive understanding
4. Avoid redundancy

Return ONLY the sub-questions, one per line, numbered 1-5."""
        
        # Call LLM with fast model
        logger.debug(f"Calling LLM tool '{llm_tool.name}' with ModelType.FAST")
        response = llm_tool.generate(prompt, ModelType.FAST)
        
        # Parse response into list of sub-questions
        sub_questions = []
        for line in response.strip().split('\n'):
            line = line.strip()
            # Remove numbering (e.g., "1. ", "1) ", etc.)
            if line and len(line) > 3:
                # Remove leading numbers and punctuation
                cleaned = line.lstrip('0123456789.)-• ').strip()
                if cleaned:
                    sub_questions.append(cleaned)
        
        # Ensure we have 3-5 questions
        if len(sub_questions) < 3:
            logger.warning(f"Only generated {len(sub_questions)} sub-questions, expected 3-5")
        
        state["research_plan"] = sub_questions[:5]  # Cap at 5
        
        # Log successful tool usage
        log_tool_success(
            state,
            node="planner",
            tool_category="llm",
            tool_name=llm_tool.name,
            metadata={"sub_questions_count": len(state["research_plan"])}
        )
        
        logger.info(f"Generated {len(state['research_plan'])} sub-questions")
        
    except Exception as e:
        logger.error(f"Planner node failed: {e}")
        log_tool_failure(
            state,
            node="planner",
            tool_category="llm",
            tool_name=getattr(llm_tool, 'name', 'unknown') if 'llm_tool' in locals() else 'unknown',
            error_msg=str(e)
        )
        state["research_plan"] = []
    
    return state



def retrieval_node(state: ResearchState, registry: ToolRegistry) -> ResearchState:
    """
    Retrieval node: Searches for and scrapes content for each sub-question.
    
    Iterates through search tools until successful, collects URLs, then
    iterates through scraper tools to extract content. Continues with
    partial results if some tools fail.
    
    Args:
        state: Current research state
        registry: Tool registry for accessing search and scraper tools
    
    Returns:
        Updated state with retrieved_documents populated
    
    Requirements: 4.2, 7.5, 8.5, 11.1, 11.2
    """
    logger.info(f"Retrieval node: Processing {len(state.get('research_plan', []))} sub-questions")
    
    research_plan = state.get("research_plan", [])
    if not research_plan:
        logger.warning("No research plan available, skipping retrieval")
        return state
    
    all_urls = []
    
    # For each sub-question, search for relevant URLs
    for idx, sub_question in enumerate(research_plan):
        logger.debug(f"Searching for sub-question {idx + 1}: {sub_question}")
        
        # Get search tool chain from registry
        search_chain = registry.get_tool_chain("search")
        
        if not search_chain:
            logger.error("No search tools available in registry")
            log_tool_failure(
                state,
                node="retrieval",
                tool_category="search",
                tool_name="unknown",
                error_msg="No search tools registered"
            )
            continue
        
        # Try each search tool until one succeeds
        search_results = []
        for search_tool in search_chain:
            try:
                logger.debug(f"Trying search tool: {search_tool.name}")
                results = search_tool.search(sub_question, max_results=5)
                
                if results:
                    search_results = results
                    log_tool_success(
                        state,
                        node="retrieval",
                        tool_category="search",
                        tool_name=search_tool.name,
                        metadata={
                            "sub_question": sub_question,
                            "results_count": len(results)
                        }
                    )
                    logger.info(f"Search tool '{search_tool.name}' returned {len(results)} results")
                    break
                else:
                    logger.debug(f"Search tool '{search_tool.name}' returned no results")
                    
            except Exception as e:
                logger.warning(f"Search tool '{search_tool.name}' failed: {e}")
                log_tool_failure(
                    state,
                    node="retrieval",
                    tool_category="search",
                    tool_name=search_tool.name,
                    error_msg=str(e),
                    metadata={"sub_question": sub_question}
                )
                continue
        
        # Collect top 5 URLs from successful search
        for result in search_results[:5]:
            if hasattr(result, 'url'):
                all_urls.append({
                    "url": result.url,
                    "title": getattr(result, 'title', ''),
                    "snippet": getattr(result, 'snippet', ''),
                    "sub_question": sub_question
                })
    
    logger.info(f"Collected {len(all_urls)} URLs to scrape")
    
    # Get scraper tool chain from registry
    scraper_chain = registry.get_tool_chain("scraper")
    
    if not scraper_chain:
        logger.error("No scraper tools available in registry")
        log_tool_failure(
            state,
            node="retrieval",
            tool_category="scraper",
            tool_name="unknown",
            error_msg="No scraper tools registered"
        )
        return state
    
    # Scrape content from each URL
    for url_info in all_urls:
        url = url_info["url"]
        logger.debug(f"Scraping URL: {url}")
        
        # Try each scraper tool until one succeeds
        scraped = False
        for scraper_tool in scraper_chain:
            try:
                logger.debug(f"Trying scraper tool: {scraper_tool.name}")
                scraped_content = scraper_tool.scrape(url)
                
                if scraped_content and scraped_content.success and scraped_content.content:
                    # Store successful scrape
                    state["retrieved_documents"].append({
                        "url": url,
                        "content": scraped_content.content,
                        "title": url_info.get("title", ""),
                        "source_tool": scraper_tool.name,
                        "sub_question": url_info.get("sub_question", "")
                    })
                    
                    log_tool_success(
                        state,
                        node="retrieval",
                        tool_category="scraper",
                        tool_name=scraper_tool.name,
                        metadata={
                            "url": url,
                            "content_length": len(scraped_content.content)
                        }
                    )
                    
                    logger.info(f"Scraper '{scraper_tool.name}' successfully extracted content from {url}")
                    scraped = True
                    break
                else:
                    error_msg = getattr(scraped_content, 'error_msg', 'No content extracted')
                    logger.debug(f"Scraper '{scraper_tool.name}' failed: {error_msg}")
                    
            except Exception as e:
                logger.warning(f"Scraper tool '{scraper_tool.name}' failed for {url}: {e}")
                log_tool_failure(
                    state,
                    node="retrieval",
                    tool_category="scraper",
                    tool_name=scraper_tool.name,
                    error_msg=str(e),
                    metadata={"url": url}
                )
                continue
        
        if not scraped:
            logger.warning(f"All scraper tools failed for URL: {url}")
    
    logger.info(f"Retrieved {len(state['retrieved_documents'])} documents")
    
    return state



def reflection_node(state: ResearchState, registry: ToolRegistry) -> ResearchState:
    """
    Reflection node: Evaluates research completeness and identifies gaps.
    
    Uses a balanced LLM to analyze retrieved documents against the original
    query and research plan, identifying any missing information.
    
    Args:
        state: Current research state
        registry: Tool registry for accessing LLM
    
    Returns:
        Updated state with gaps_identified and incremented research_loop_count
    
    Requirements: 4.3, 5.4, 11.1
    """
    logger.info("Reflection node: Evaluating research completeness")
    
    # Increment loop count
    state["research_loop_count"] += 1
    
    try:
        # Request balanced LLM from registry
        llm_tool = registry.get_tool("llm")
        
        if not llm_tool:
            logger.error("No LLM tool available in registry")
            log_tool_failure(
                state,
                node="reflection",
                tool_category="llm",
                tool_name="unknown",
                error_msg="No LLM tool registered"
            )
            # Assume complete if no LLM available
            state["gaps_identified"] = ""
            return state
        
        # Build context for LLM
        original_query = state["original_query"]
        research_plan = state.get("research_plan", [])
        retrieved_docs = state.get("retrieved_documents", [])
        
        # Create document summaries
        doc_summaries = []
        for idx, doc in enumerate(retrieved_docs[:10]):  # Limit to first 10 for context
            content_preview = doc.get("content", "")[:500]  # First 500 chars
            doc_summaries.append(
                f"Document {idx + 1} ({doc.get('title', 'Untitled')}):\n{content_preview}..."
            )
        
        docs_text = "\n\n".join(doc_summaries) if doc_summaries else "No documents retrieved yet."
        plan_text = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(research_plan))
        
        # Generate prompt for gap identification
        prompt = f"""You are a research quality evaluator. Analyze whether the retrieved information is sufficient to answer the research query comprehensively.

Original Research Query: {original_query}

Research Plan (Sub-questions):
{plan_text}

Retrieved Documents ({len(retrieved_docs)} total):
{docs_text}

Task: Determine if the retrieved information is sufficient to answer the original query and all sub-questions comprehensively.

If there are significant information gaps, describe them specifically (e.g., "Missing information about X", "Need more details on Y").

If the information is sufficient, respond with: "COMPLETE"

Your response:"""
        
        # Call LLM with balanced model
        logger.debug(f"Calling LLM tool '{llm_tool.name}' with ModelType.BALANCED")
        response = llm_tool.generate(prompt, ModelType.BALANCED)
        
        # Check if research is complete
        response_clean = response.strip().upper()
        if "COMPLETE" in response_clean and len(response_clean) < 50:
            state["gaps_identified"] = ""
            logger.info("Reflection: Research is complete")
        else:
            state["gaps_identified"] = response.strip()
            logger.info(f"Reflection: Gaps identified - {response.strip()[:100]}...")
        
        # Log successful tool usage
        log_tool_success(
            state,
            node="reflection",
            tool_category="llm",
            tool_name=llm_tool.name,
            metadata={
                "loop_count": state["research_loop_count"],
                "documents_analyzed": len(retrieved_docs),
                "gaps_found": bool(state["gaps_identified"])
            }
        )
        
    except Exception as e:
        logger.error(f"Reflection node failed: {e}")
        log_tool_failure(
            state,
            node="reflection",
            tool_category="llm",
            tool_name=getattr(llm_tool, 'name', 'unknown') if 'llm_tool' in locals() else 'unknown',
            error_msg=str(e)
        )
        # Assume complete on failure to avoid infinite loops
        state["gaps_identified"] = ""
    
    return state



def synthesis_node(state: ResearchState, registry: ToolRegistry) -> ResearchState:
    """
    Synthesis node: Generates final structured report with citations.
    
    Uses a powerful LLM to synthesize all retrieved information into a
    comprehensive report with inline citations and a references section.
    
    Args:
        state: Current research state
        registry: Tool registry for accessing LLM
    
    Returns:
        Updated state with final_report populated
    
    Requirements: 4.4, 12.2, 12.3, 12.4, 12.5
    """
    logger.info("Synthesis node: Generating final report")
    
    try:
        # Request powerful LLM from registry
        llm_tool = registry.get_tool("llm")
        
        if not llm_tool:
            logger.error("No LLM tool available in registry")
            log_tool_failure(
                state,
                node="synthesis",
                tool_category="llm",
                tool_name="unknown",
                error_msg="No LLM tool registered"
            )
            state["final_report"] = "Error: Unable to generate report - no LLM tool available"
            return state
        
        # Build context for synthesis
        original_query = state["original_query"]
        research_plan = state.get("research_plan", [])
        retrieved_docs = state.get("retrieved_documents", [])
        
        # Limit documents to avoid context window issues (max 15 docs)
        max_docs_for_synthesis = 15
        docs_to_use = retrieved_docs[:max_docs_for_synthesis]
        
        # Create numbered document references with limited content
        doc_references = []
        for idx, doc in enumerate(docs_to_use):
            # Limit content to 300 characters per document to stay within context limits
            content = doc.get('content', '')
            content_preview = content[:300] + "..." if len(content) > 300 else content
            
            doc_references.append(
                f"[{idx + 1}] {doc.get('title', 'Untitled')}\n"
                f"URL: {doc.get('url', 'N/A')}\n"
                f"Content: {content_preview}\n"
            )
        
        docs_text = "\n".join(doc_references) if doc_references else "No documents available."
        plan_text = "\n".join(f"- {q}" for q in research_plan)
        
        # Generate synthesis prompt
        prompt = f"""You are a research synthesis expert. Create a comprehensive, well-structured research report based on the retrieved information.

Original Research Query: {original_query}

Research Plan:
{plan_text}

Retrieved Documents:
{docs_text}

Instructions:
1. Write a comprehensive report that answers the original query
2. Use inline citations [1], [2], etc. to reference specific documents
3. Organize the report with clear sections
4. Include a "References" section at the end listing all sources
5. Ensure all claims are supported by citations
6. Write in a clear, professional style

Format:
# [Title]

## Summary
[Brief overview]

## [Section 1]
[Content with citations [1], [2]]

## [Section 2]
[Content with citations]

## References
[1] Title - URL
[2] Title - URL

Generate the report:"""
        
        # Try structured output first
        try:
            logger.debug(f"Attempting structured output with CitedReport schema")
            response = llm_tool.generate(
                prompt,
                ModelType.POWERFUL,
                structured_output_schema=CitedReport
            )
            
            # If structured output succeeded, format it
            if isinstance(response, CitedReport):
                report_parts = [f"# {response.title}\n"]
                report_parts.append(f"## Summary\n{response.summary}\n")
                
                for section in response.sections:
                    report_parts.append(f"## {section.heading}\n{section.content}\n")
                
                report_parts.append("## References\n")
                for citation in response.references:
                    report_parts.append(f"[{citation.id}] {citation.title} - {citation.url}\n")
                
                state["final_report"] = "\n".join(report_parts)
                logger.info("Generated structured report successfully")
            else:
                # Fallback to unstructured
                state["final_report"] = str(response)
                logger.info("Generated unstructured report")
                
        except Exception as struct_error:
            # Fall back to unstructured generation
            logger.warning(f"Structured output failed, falling back to unstructured: {struct_error}")
            response = llm_tool.generate(prompt, ModelType.POWERFUL)
            state["final_report"] = response
            logger.info("Generated unstructured report as fallback")
        
        # Log successful tool usage
        log_tool_success(
            state,
            node="synthesis",
            tool_category="llm",
            tool_name=llm_tool.name,
            metadata={
                "documents_synthesized": len(retrieved_docs),
                "report_length": len(state["final_report"])
            }
        )
        
        logger.info(f"Final report generated ({len(state['final_report'])} characters)")
        
    except Exception as e:
        logger.error(f"Synthesis node failed: {e}")
        log_tool_failure(
            state,
            node="synthesis",
            tool_category="llm",
            tool_name=getattr(llm_tool, 'name', 'unknown') if 'llm_tool' in locals() else 'unknown',
            error_msg=str(e)
        )
        state["final_report"] = f"Error generating report: {str(e)}"
    
    return state



def should_continue_research(state: ResearchState) -> str:
    """
    Conditional routing function for research workflow.
    
    Determines whether to continue research loop or proceed to synthesis
    based on gap identification and loop count.
    
    Args:
        state: Current research state
    
    Returns:
        "continue" to loop back to retrieval, "synthesize" to proceed to synthesis
    
    Requirements: 6.4
    """
    gaps_identified = state.get("gaps_identified", "")
    research_loop_count = state.get("research_loop_count", 0)
    max_loops = state.get("max_loops", 3)
    
    # Check if gaps exist and we haven't exceeded max loops
    has_gaps = bool(gaps_identified and gaps_identified.strip())
    below_max = research_loop_count < max_loops
    
    if has_gaps and below_max:
        logger.info(
            f"Continuing research: gaps found, loop {research_loop_count}/{max_loops}"
        )
        return "continue"
    else:
        if not has_gaps:
            logger.info("Proceeding to synthesis: research complete")
        else:
            logger.info(
                f"Proceeding to synthesis: max loops reached ({research_loop_count}/{max_loops})"
            )
        return "synthesize"
