# Agentic Claim Verification Architecture

## A Recursive Multi-Agent System for Comprehensive Fact-Checking

---

## Executive Summary

This document presents a complete agentic architecture for claim verification that mimics elite investigative journalism methodology. The system employs recursive multi-agent workflows using web tools (Exa, Tavily, Perplexity, etc.) to provide comprehensive, timeline-aware claim analysis with adaptive depth.

---

## I. Core Philosophy: The Three Pillars

### 1. **Thoroughness** - Never Trust, Always Verify

- Assume all sources are potentially wrong until independently validated
- Pursue primary evidence over secondary interpretations
- Verify every assertion, name, date, and statistic
- Cross-reference across multiple independent sources

### 2. **Adaptability** - Context-Driven Investigation

- Adjust search depth based on claim complexity
- Deploy specialized tools for different evidence types (text, images, video, statistics)
- Recognize when to recurse deeper vs. when sufficient evidence exists
- Shift from reactive to proactive investigation patterns

### 3. **Transparency** - Auditable Reasoning

- Document all search queries and source evaluations
- Provide explicit reasoning chains
- Cite specific evidence with confidence scores
- Flag contradictions and knowledge gaps

---

## II. The Seven-Stage Verification Lifecycle (Adapted for Agents)

```
┌─────────────────────────────────────────────────────────────┐
│                  CLAIM VERIFICATION LIFECYCLE                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Stage 1: Claim Deconstruction & Prioritization             │
│           └─> Extract verifiable sub-claims                  │
│           └─> Identify claim type & complexity               │
│           └─> Determine investigation depth needed           │
│                                                               │
│  Stage 2: Primary Source Acquisition                         │
│           └─> Official records, reports, databases           │
│           └─> Direct document retrieval                      │
│           └─> Government/institutional data                  │
│                                                               │
│  Stage 3: Expert & Secondary Source Acquisition              │
│           └─> Academic research & peer review                │
│           └─> Domain expert statements                       │
│           └─> Credible news organization reporting           │
│                                                               │
│  Stage 4: Data Analysis & Cross-Validation                   │
│           └─> Statistical verification                       │
│           └─> Temporal consistency checks                    │
│           └─> Logical coherence analysis                     │
│                                                               │
│  Stage 5: Digital Forensics & OSINT                          │
│           └─> Image/video verification                       │
│           └─> Geolocation & chronolocation                   │
│           └─> Network propagation analysis                   │
│                                                               │
│  Stage 6: Evidence Synthesis & Assessment                    │
│           └─> Confidence scoring                             │
│           └─> Contradiction resolution                       │
│           └─> Final verdict assignment                       │
│                                                               │
│  Stage 7: Result Formatting & Source Attribution             │
│           └─> Timeline construction                          │
│           └─> Source hierarchy display                       │
│           └─> Uncertainty communication                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## III. Agentic Architecture: Hierarchical Multi-Agent System

### A. Agent Hierarchy

```
                    ┌──────────────────────┐
                    │  ORCHESTRATOR AGENT  │
                    │   (Claim Director)   │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
        ┌───────▼─────┐  ┌────▼─────┐  ┌────▼──────┐
        │ DECOMPOSER  │  │ PLANNER  │  │ EVALUATOR │
        │   AGENT     │  │  AGENT   │  │   AGENT   │
        └───────┬─────┘  └────┬─────┘  └────┬──────┘
                │              │              │
                └──────────────┼──────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼────────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │ PRIMARY SOURCE │  │  SECONDARY  │  │  FORENSIC   │
    │  RETRIEVAL     │  │   SOURCE    │  │  ANALYSIS   │
    │    AGENTS      │  │  RETRIEVAL  │  │   AGENTS    │
    └────────────────┘  └─────────────┘  └─────────────┘
            │                  │                  │
    ┌───────┴─────┬────────────┴──────┬──────────┴───────┐
    │             │            │       │          │       │
┌───▼──┐  ┌──────▼──┐  ┌─────▼──┐ ┌──▼───┐  ┌───▼───┐ ┌▼────┐
│ Exa  │  │ Tavily  │  │Official│ │Expert│  │ Image │ │Geol.│
│Search│  │ Search  │  │  APIs  │ │Search│  │Verify │ │Check│
└──────┘  └─────────┘  └────────┘ └──────┘  └───────┘ └─────┘
```

### B. Agent Roles & Responsibilities

#### 1. **Orchestrator Agent** (Claim Director)

**Purpose**: Manages entire verification workflow and recursive decisions

**Core Functions**:

- Receives initial claim input
- Coordinates all sub-agents
- Makes recursion decisions (continue investigating vs. conclude)
- Assembles final comprehensive report
- Manages investigation budget (API calls, time limits)

**Decision Framework**:

```python
def should_recurse(current_evidence, confidence, depth):
    if depth >= MAX_DEPTH:
        return False
    if confidence >= CONFIDENCE_THRESHOLD:
        return False
    if contradictions_exist(current_evidence):
        return True
    if knowledge_gaps_critical(current_evidence):
        return True
    if temporal_inconsistencies(current_evidence):
        return True
    return False
```

#### 2. **Decomposer Agent**

**Purpose**: Breaks down complex claims into atomic, verifiable sub-claims

**Process**:

1. Parse claim into logical components
2. Identify factual assertions vs. opinions
3. Extract entities (people, places, dates, statistics)
4. Tag claim type (factual, statistical, contextual, multimedia)
5. Prioritize sub-claims by verifiability and impact

**Example**:

```
Input Claim: "President Biden announced a $2 trillion infrastructure plan
              in March 2021, the largest in US history."

Decomposed Sub-Claims:
├─ C1: Biden announced an infrastructure plan [FACTUAL]
├─ C2: The plan was worth $2 trillion [STATISTICAL]
├─ C3: The announcement occurred in March 2021 [TEMPORAL]
└─ C4: It is the largest in US history [COMPARATIVE]
    └─ C4.1: What were previous infrastructure plans? [RESEARCH NEEDED]
    └─ C4.2: How is "largest" defined? (cost? scope?) [CLARIFICATION]
```

#### 3. **Planner Agent**

**Purpose**: Creates optimal search strategy for each sub-claim

**Strategy Selection**:

- **Simple factual claims** → 1-2 search queries, focus on primary sources
- **Statistical claims** → Multiple queries + database verification
- **Complex comparative claims** → Recursive deep dive with timeline construction
- **Multimedia claims** → Forensic tool deployment first

**Output**: Prioritized search queue with tool assignments

```json
{
  "sub_claim_id": "C2",
  "search_plan": [
    {
      "tool": "tavily",
      "query": "Biden infrastructure plan amount 2021",
      "priority": 1
    },
    {
      "tool": "official_api",
      "source": "whitehouse.gov",
      "endpoint": "press-releases",
      "priority": 1
    },
    {
      "tool": "exa",
      "query": "Biden American Jobs Plan cost",
      "priority": 2,
      "temporal_filter": "2021-03"
    }
  ],
  "expected_evidence_type": [
    "official_statement",
    "news_reporting",
    "fact_check"
  ],
  "recursion_likely": false
}
```

#### 4. **Evaluator Agent**

**Purpose**: Assesses source quality and evidence reliability

**Source Evaluation Matrix**:

```
┌─────────────────────────────────────────────────────────────┐
│              SOURCE RELIABILITY SCORING                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Tier 1: PRIMARY SOURCES (Score: 9-10)                       │
│  • Official government documents/databases                   │
│  • Direct statements from authoritative entities             │
│  • Original research data                                    │
│  • Legal filings, regulatory records                         │
│                                                               │
│ Tier 2: EXPERT SOURCES (Score: 7-8)                         │
│  • Peer-reviewed academic research                           │
│  • Accredited expert testimony                              │
│  • Established fact-checking organizations                   │
│                                                               │
│ Tier 3: CREDIBLE NEWS (Score: 5-6)                          │
│  • Major news organizations with standards                   │
│  • Investigative journalism with multiple sources            │
│  • Cross-validated reporting                                 │
│                                                               │
│ Tier 4: SECONDARY ANALYSIS (Score: 3-4)                     │
│  • Opinion pieces with citations                             │
│  • Aggregator sites referencing primary sources              │
│  • Blog posts from domain experts                            │
│                                                               │
│ Tier 5: UNRELIABLE (Score: 1-2)                             │
│  • Anonymous sources without corroboration                   │
│  • Known bias outlets without fact-checking                  │
│  • Social media posts                                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Bias Detection**:

- Narrative bias: How the story is framed
- Selection bias: Which events are covered/omitted
- Temporal bias: Coverage patterns over time

#### 5. **Primary Source Retrieval Agents**

**Purpose**: Gather direct, authoritative evidence

**Tool Specializations**:

**Exa Agent**:

- Semantic search for official documents
- Academic paper retrieval
- High-precision domain filtering
- Temporal search with exact date ranges

**Tavily Agent**:

- Broad web search for initial discovery
- Real-time news aggregation
- Multi-source cross-referencing
- Quick fact verification

**Official API Agent**:

- Direct database queries (government data, company filings)
- Structured data retrieval
- Historical record access
- Archival document fetching

#### 6. **Secondary Source Retrieval Agents**

**Purpose**: Gather expert analysis and contextual information

**Expert Search Agent**:

- Academic researcher identification
- Domain expert statements
- Professional organization positions
- Industry analyst reports

**News Aggregation Agent**:

- Cross-organization reporting patterns
- Timeline construction from multiple outlets
- Contradiction detection
- Source diversity maximization

#### 7. **Forensic Analysis Agents**

**Purpose**: Verify multimedia and digital evidence

**Image Verification Agent**:

- Reverse image search
- EXIF metadata extraction
- Manipulation detection
- Visual similarity matching

**Geolocation Agent**:

- Landmark identification
- Satellite imagery cross-reference
- Shadow/weather analysis
- Coordinate verification

**Chronolocation Agent**:

- First appearance detection
- Publication timeline mapping
- Temporal consistency checking
- Archive verification

---

## IV. Recursive Investigation Algorithm

### A. The Core Recursion Logic

```python
class ClaimVerificationOrchestrator:
    def __init__(self, max_depth=5, confidence_threshold=0.85):
        self.max_depth = max_depth
        self.confidence_threshold = confidence_threshold
        self.investigation_tree = {}

    def verify_claim(self, claim, current_depth=0):
        """
        Recursive claim verification with adaptive depth
        """
        # Base cases
        if current_depth >= self.max_depth:
            return self.compile_results("MAX_DEPTH_REACHED")

        # Stage 1: Decompose claim
        sub_claims = self.decomposer_agent.decompose(claim)

        # Stage 2-3: Plan and execute searches
        evidence_collection = {}
        for sub_claim in sub_claims:
            search_plan = self.planner_agent.create_plan(sub_claim)
            evidence = self.execute_search_plan(search_plan)
            evidence_collection[sub_claim.id] = evidence

        # Stage 4: Evaluate evidence
        evaluation = self.evaluator_agent.assess(evidence_collection)

        # RECURSION DECISION POINT
        recursion_needed = self.determine_recursion_needs(
            evaluation,
            current_depth
        )

        if recursion_needed:
            # Identify knowledge gaps requiring deeper investigation
            deeper_claims = self.identify_knowledge_gaps(evaluation)

            for deeper_claim in deeper_claims:
                # RECURSIVE CALL with increased depth
                sub_result = self.verify_claim(
                    deeper_claim,
                    current_depth + 1
                )
                evidence_collection[deeper_claim.id] = sub_result

        # Stage 5: Forensic analysis (if multimedia present)
        if self.contains_multimedia(claim):
            forensic_results = self.forensic_agents.analyze(claim)
            evidence_collection['forensic'] = forensic_results

        # Stage 6: Final synthesis
        final_verdict = self.synthesize_evidence(evidence_collection)

        # Stage 7: Format results
        return self.format_comprehensive_report(
            claim,
            evidence_collection,
            final_verdict,
            current_depth
        )

    def determine_recursion_needs(self, evaluation, depth):
        """
        Decide if deeper investigation needed
        """
        # Check confidence level
        if evaluation.confidence < self.confidence_threshold:
            return True

        # Check for contradictions
        if evaluation.has_contradictions:
            return True

        # Check for knowledge gaps in critical areas
        if evaluation.critical_gaps:
            return True

        # Check for temporal inconsistencies
        if evaluation.timeline_conflicts:
            return True

        # Check for source quality issues
        if evaluation.primary_source_count == 0 and depth == 0:
            return True

        return False

    def identify_knowledge_gaps(self, evaluation):
        """
        Generate new claims to investigate based on gaps
        """
        new_claims = []

        # Missing context
        if evaluation.context_missing:
            new_claims.extend(
                self.generate_context_queries(evaluation)
            )

        # Contradictory evidence
        if evaluation.contradictions:
            new_claims.extend(
                self.generate_contradiction_resolution_queries(
                    evaluation.contradictions
                )
            )

        # Timeline gaps
        if evaluation.timeline_gaps:
            new_claims.extend(
                self.generate_timeline_fill_queries(
                    evaluation.timeline_gaps
                )
            )

        # Comparative claims needing baseline
        if evaluation.needs_comparison:
            new_claims.extend(
                self.generate_comparison_queries(evaluation)
            )

        return new_claims
```

### B. Search Strategy Matrix

| Claim Type            | Initial Search Tools   | Recursion Triggers      | Max Depth |
| --------------------- | ---------------------- | ----------------------- | --------- |
| **Simple Factual**    | Tavily → Official API  | No primary source found | 2         |
| **Statistical**       | Exa → Database API     | Number contradictions   | 3         |
| **Temporal**          | Tavily + Timeline      | Date inconsistencies    | 3         |
| **Comparative**       | Exa → Multiple queries | Missing baseline data   | 4         |
| **Contextual**        | Multiple tools         | Missing background      | 4         |
| **Multimedia**        | Forensic tools first   | Visual contradictions   | 3         |
| **Complex Composite** | All tools              | Multiple gaps           | 5         |

### C. Example: Recursive Investigation Flow

**Initial Claim**: "The 2020 US election had the highest voter turnout in history."

**Depth 0 - Initial Investigation**:

```
Decomposer Output:
├─ C1: 2020 US election occurred
├─ C2: Voter turnout was measured
├─ C3: Turnout was "highest in history"
    └─ Requires comparison baseline [RECURSION TRIGGER]

Planner Strategy:
└─ Search "2020 US election voter turnout statistics"
└─ Search "historical US voter turnout data"

Evidence Found:
├─ Source 1: Census Bureau (Tier 1) - "66.8% turnout in 2020"
├─ Source 2: Multiple news (Tier 3) - "Highest turnout percentage since 1900"
└─ Source 3: Fact-check site (Tier 2) - "Depends on metric used"

Evaluator Decision:
├─ Confidence: 0.65 (below threshold)
├─ Issue: "Highest" is ambiguous (percentage vs. absolute numbers)
└─ RECURSION NEEDED: Clarify comparison methodology
```

**Depth 1 - Recursive Investigation** (Addressing ambiguity):

```
New Sub-Claims Generated:
├─ C3.1: What metric defines "highest"? (percentage vs. total votes)
├─ C3.2: What were historical turnout percentages?
├─ C3.3: What were historical absolute vote counts?

Planner Strategy:
└─ Database query: US Census historical voter data
└─ Exa search: "voter turnout percentage by year US elections"
└─ Exa search: "total votes cast US presidential elections history"

Evidence Found:
├─ 2020: 158.4M votes, 66.8% turnout
├─ 2016: 138.8M votes, 59.2% turnout
├─ 1960: 68.8M votes, 62.8% turnout
├─ 1876: 8.4M votes, 81.8% turnout

Evaluator Decision:
├─ Confidence: 0.92 (above threshold)
├─ Verdict: PARTIALLY TRUE
│   └─ Highest absolute vote count: TRUE
│   └─ Highest percentage turnout: FALSE (1876 was higher)
└─ RECURSION NOT NEEDED: Sufficient evidence
```

**Depth 2 - Optional Context Enrichment**:

```
Optional Deeper Investigation (if triggered):
├─ C3.4: Why was 1876 turnout so high?
├─ C3.5: How has voter eligibility changed over time?
└─ C3.6: What factors drive turnout variation?

This would only trigger if:
- User requests full context
- High-stakes verification needed
- Educational report required
```

---

## V. Timeline Construction & Event Mapping

### A. Temporal Analysis Agent

**Purpose**: Build chronological event sequences from distributed evidence

**Process**:

1. Extract all temporal markers from evidence
2. Normalize date formats and resolve ambiguities
3. Cross-reference events across sources
4. Identify causal relationships
5. Flag temporal contradictions
6. Construct unified timeline

**Example Output**:

```
CLAIM: "President Biden's infrastructure plan evolved significantly
        before passage."

TIMELINE CONSTRUCTION:
┌────────────────────────────────────────────────────────────┐
│ 2021-03-31: Initial proposal - "American Jobs Plan"        │
│  Source: White House press release (Tier 1)                │
│  Amount: $2.3 trillion                                      │
│  Scope: Infrastructure + care economy                       │
│                                                              │
│ 2021-04-28: Revised proposal after GOP negotiations        │
│  Source: White House statements (Tier 1)                   │
│  Amount: Reduced to $1.7 trillion                          │
│  Scope: Narrowed focus                                      │
│                                                              │
│ 2021-07-28: Bipartisan Infrastructure Framework agreed     │
│  Source: Senate records (Tier 1)                           │
│  Amount: Further reduced to $1.2 trillion                  │
│  Scope: Traditional infrastructure only                     │
│                                                              │
│ 2021-08-10: Senate passes Infrastructure Investment Act    │
│  Source: Congressional Record (Tier 1)                     │
│  Final amount: $1.2 trillion ($550B new spending)          │
│                                                              │
│ 2021-11-15: House passes bill, Biden signs into law        │
│  Source: Federal Register (Tier 1)                         │
│                                                              │
│ CONTRADICTIONS DETECTED:                                    │
│  ⚠ Some news outlets report "$2 trillion plan" in Nov      │
│     Resolution: Confusing initial proposal with final bill  │
│                                                              │
│ CONFIDENCE: 0.95 (High - multiple Tier 1 sources align)    │
└────────────────────────────────────────────────────────────┘
```

### B. Multi-Event Timeline Synthesis

When claims involve multiple related events:

```python
class TimelineConstructor:
    def build_comprehensive_timeline(self, claim, evidence_set):
        """
        Construct multi-source, cross-validated timeline
        """
        timeline = []

        # Extract all temporal events
        for evidence in evidence_set:
            events = self.extract_temporal_events(evidence)
            timeline.extend(events)

        # Normalize and deduplicate
        timeline = self.normalize_dates(timeline)
        timeline = self.deduplicate_events(timeline)

        # Cross-validate across sources
        validated_timeline = []
        for event in timeline:
            corroborating_sources = self.find_corroboration(
                event,
                evidence_set
            )

            if len(corroborating_sources) >= 2 or \
               self.is_tier_1_source(event.source):
                event.confidence = self.calculate_confidence(
                    corroborating_sources
                )
                validated_timeline.append(event)
            else:
                # Recursion trigger: Need more sources
                additional_evidence = self.search_for_corroboration(event)
                if additional_evidence:
                    validated_timeline.append(event)
                else:
                    event.confidence = 0.3
                    event.flag = "SINGLE_SOURCE_UNVERIFIED"
                    validated_timeline.append(event)

        # Sort chronologically
        validated_timeline.sort(key=lambda e: e.date)

        # Identify contradictions
        contradictions = self.detect_contradictions(validated_timeline)

        if contradictions:
            # Recursion trigger: Resolve contradictions
            resolution = self.resolve_contradictions(contradictions)
            validated_timeline = self.apply_resolutions(
                validated_timeline,
                resolution
            )

        return validated_timeline
```

---

## VI. Contradiction Resolution Framework

### A. Contradiction Types & Resolution Strategies

```
┌─────────────────────────────────────────────────────────────┐
│           CONTRADICTION RESOLUTION MATRIX                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ TYPE 1: NUMERICAL CONTRADICTIONS                            │
│  Example: Source A says "$2T", Source B says "$1.2T"        │
│  Resolution Strategy:                                        │
│   1. Check source dates (may be different proposals)        │
│   2. Check primary sources (which is authoritative?)        │
│   3. Search for clarifying context                          │
│   4. If unresolvable: Report range with confidence scores   │
│                                                               │
│ TYPE 2: TEMPORAL CONTRADICTIONS                             │
│  Example: Event dated as "March 2021" vs "April 2021"       │
│  Resolution Strategy:                                        │
│   1. Favor Tier 1 sources (official records)                │
│   2. Check for timezone differences                          │
│   3. Look for announcement vs. implementation dates          │
│   4. Recursive search for authoritative timeline             │
│                                                               │
│ TYPE 3: CONTEXTUAL CONTRADICTIONS                           │
│  Example: Quote used in different contexts                   │
│  Resolution Strategy:                                        │
│   1. Find original full statement                            │
│   2. Analyze surrounding context                             │
│   3. Check for selective editing                             │
│   4. Flag if context materially alters meaning               │
│                                                               │
│ TYPE 4: SOURCE CREDIBILITY CONFLICTS                        │
│  Example: Tier 1 vs Tier 3 sources disagree                 │
│  Resolution Strategy:                                        │
│   1. Always favor higher-tier source                         │
│   2. Search for additional Tier 1/2 sources                  │
│   3. Investigate potential bias in lower-tier source         │
│   4. Document disagreement with confidence penalties         │
│                                                               │
│ TYPE 5: DEFINITIONAL AMBIGUITY                              │
│  Example: "Largest" measured differently                     │
│  Resolution Strategy:                                        │
│   1. Clarify all possible definitions                        │
│   2. Evaluate claim under each definition                    │
│   3. Report results for each interpretation                  │
│   4. Flag ambiguity in final verdict                         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### B. Contradiction Resolution Algorithm

```python
class ContradictionResolver:
    def resolve(self, contradiction_set):
        """
        Systematically resolve contradictions between sources
        """
        resolutions = []

        for contradiction in contradiction_set:
            # Classify contradiction type
            c_type = self.classify_contradiction(contradiction)

            # Apply type-specific resolution strategy
            if c_type == "NUMERICAL":
                resolution = self.resolve_numerical(contradiction)
            elif c_type == "TEMPORAL":
                resolution = self.resolve_temporal(contradiction)
            elif c_type == "CONTEXTUAL":
                resolution = self.resolve_contextual(contradiction)
            elif c_type == "SOURCE_CREDIBILITY":
                resolution = self.resolve_by_source_tier(contradiction)
            elif c_type == "DEFINITIONAL":
                resolution = self.resolve_definitional(contradiction)

            # If resolution requires more evidence, trigger recursion
            if resolution.needs_more_evidence:
                additional_evidence = self.search_for_resolution(
                    contradiction,
                    resolution.search_suggestions
                )
                resolution = self.reattempt_resolution(
                    contradiction,
                    additional_evidence
                )

            resolutions.append(resolution)

        return resolutions

    def resolve_numerical(self, contradiction):
        """
        Resolve numerical discrepancies
        """
        # Extract all numerical values and their sources
        values = [(v.number, v.source, v.date) for v in contradiction.values]

        # Sort by source tier
        values.sort(key=lambda x: self.source_tier(x[1]), reverse=True)

        # Check if temporal progression explains difference
        if self.is_temporal_progression(values):
            return Resolution(
                type="TEMPORAL_PROGRESSION",
                explanation="Values evolved over time",
                timeline=self.construct_value_timeline(values),
                confidence=0.9
            )

        # Check if definitional difference explains it
        if self.check_definitional_variance(contradiction):
            return Resolution(
                type="DEFINITIONAL_DIFFERENCE",
                explanation="Different metrics used",
                clarification=self.explain_definitions(values),
                confidence=0.85
            )

        # If unresolvable, favor highest-tier source
        authoritative_value = values[0]  # Highest tier

        return Resolution(
            type="SOURCE_TIER_PREFERENCE",
            selected_value=authoritative_value[0],
            source=authoritative_value[1],
            alternatives=[v for v in values[1:]],
            confidence=self.calculate_confidence(values),
            needs_more_evidence=(len(values) == 2 and
                                self.source_tier(values[0][1]) ==
                                self.source_tier(values[1][1]))
        )
```

---

## VII. Confidence Scoring System

### A. Multi-Factor Confidence Calculation

```python
class ConfidenceScorer:
    def calculate_confidence(self, evidence_set, claim):
        """
        Calculate overall confidence score (0-1) for claim verdict
        """
        scores = {
            'source_quality': self.score_source_quality(evidence_set),
            'source_agreement': self.score_source_agreement(evidence_set),
            'source_diversity': self.score_source_diversity(evidence_set),
            'temporal_consistency': self.score_temporal_consistency(evidence_set),
            'logical_coherence': self.score_logical_coherence(evidence_set, claim),
            'primary_source_presence': self.score_primary_sources(evidence_set)
        }

        # Weighted combination
        weights = {
            'source_quality': 0.30,
            'source_agreement': 0.25,
            'source_diversity': 0.15,
            'temporal_consistency': 0.10,
            'logical_coherence': 0.10,
            'primary_source_presence': 0.10
        }

        final_confidence = sum(
            scores[factor] * weights[factor]
            for factor in scores
        )

        # Apply penalties for concerning patterns
        final_confidence *= self.apply_penalties(evidence_set)

        return min(max(final_confidence, 0.0), 1.0)

    def score_source_quality(self, evidence_set):
        """
        Average source tier score
        """
        tier_scores = {
            1: 1.0,   # Primary/Official
            2: 0.8,   # Expert/Academic
            3: 0.6,   # Credible News
            4: 0.4,   # Secondary
            5: 0.2    # Unreliable
        }

        if not evidence_set:
            return 0.0

        avg_tier_score = sum(
            tier_scores.get(e.source_tier, 0.2)
            for e in evidence_set
        ) / len(evidence_set)

        return avg_tier_score

    def score_source_agreement(self, evidence_set):
        """
        How well sources agree on the claim
        """
        if len(evidence_set) < 2:
            return 0.5  # Insufficient sources penalty

        verdicts = [e.verdict for e in evidence_set]
        most_common = max(set(verdicts), key=verdicts.count)
        agreement_ratio = verdicts.count(most_common) / len(verdicts)

        return agreement_ratio

    def score_source_diversity(self, evidence_set):
        """
        Diversity of source types (prevents echo chamber)
        """
        source_types = set(e.source_type for e in evidence_set)
        diversity_score = min(len(source_types) / 4, 1.0)  # Cap at 4 types

        return diversity_score

    def apply_penalties(self, evidence_set):
        """
        Reduce confidence for concerning patterns
        """
        penalty_multiplier = 1.0

        # No primary sources penalty
        if not any(e.source_tier == 1 for e in evidence_set):
            penalty_multiplier *= 0.8

        # Single source penalty
        if len(evidence_set) == 1:
            penalty_multiplier *= 0.7

        # Contradiction penalty
        verdicts = [e.verdict for e in evidence_set]
        if len(set(verdicts)) > 1:
            contradiction_ratio = 1 - (max(verdicts.count(v) for v in set(verdicts)) / len(verdicts))
            penalty_multiplier *= (1 - contradiction_ratio * 0.5)

        return penalty_multiplier
```

### B. Confidence Thresholds & Actions

```
┌──────────────────────────────────────────────────────────┐
│         CONFIDENCE LEVELS & RECOMMENDED ACTIONS           │
├──────────────────────────────────────────────────────────┤
│                                                            │
│ 0.90 - 1.00 │ VERY HIGH                                   │
│             │ • Multiple Tier 1 sources agree             │
│             │ • No contradictions                          │
│             │ • Strong temporal consistency                │
│             │ Action: Publish verdict with confidence     │
│                                                            │
│ 0.75 - 0.89 │ HIGH                                        │
│             │ • Mix of Tier 1-2 sources agree             │
│             │ • Minor or resolved contradictions           │
│             │ Action: Publish with documented caveats     │
│                                                            │
│ 0.60 - 0.74 │ MODERATE                                    │
│             │ • Mostly Tier 2-3 sources                   │
│             │ • Some contradictions remain                 │
│             │ Action: Flag uncertainties, present range   │
│             │        Consider recursion for key gaps      │
│                                                            │
│ 0.40 - 0.59 │ LOW                                         │
│             │ • Weak sources or major contradictions      │
│             │ • Significant knowledge gaps                 │
│             │ Action: TRIGGER RECURSION                   │
│             │        Deepen investigation                  │
│                                                            │
│ 0.00 - 0.39 │ VERY LOW                                    │
│             │ • Unreliable sources only                   │
│             │ • Conflicting evidence                       │
│             │ Action: TRIGGER RECURSION or                │
│             │        Report as UNVERIFIABLE               │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

---

## VIII. Tool Integration & API Strategy

### A. Tool Selection Matrix

| Tool              | Best For                                    | Strengths                             | Limitations                 | Priority Use Cases                       |
| ----------------- | ------------------------------------------- | ------------------------------------- | --------------------------- | ---------------------------------------- |
| **Exa**           | Semantic search, academic papers, precision | High-quality filtering, neural search | Smaller index than Google   | Finding primary sources, research papers |
| **Tavily**        | Real-time news, broad coverage              | Speed, current events                 | Less precise than Exa       | Breaking news, initial discovery         |
| **Perplexity**    | Synthesized answers, quick facts            | Pre-summarized, cited                 | Less control over sources   | Simple fact checks, quick validation     |
| **Official APIs** | Government data, company filings            | Authoritative, structured             | Limited to specific domains | Primary source acquisition               |
| **Google/Bing**   | Broadest coverage                           | Comprehensive                         | Quality varies widely       | Fallback when specialized tools fail     |

### B. Multi-Tool Search Strategy

```python
class MultiToolSearchOrchestrator:
    def execute_comprehensive_search(self, claim, search_plan):
        """
        Execute searches across multiple tools in parallel
        """
        search_tasks = []

        for query_spec in search_plan.queries:
            # Route to appropriate tool
            if query_spec.requires_precision:
                search_tasks.append(
                    self.exa_agent.search(
                        query=query_spec.query,
                        num_results=query_spec.depth,
                        include_domains=query_spec.preferred_domains,
                        start_published_date=query_spec.after_date
                    )
                )

            if query_spec.requires_breadth:
                search_tasks.append(
                    self.tavily_agent.search(
                        query=query_spec.query,
                        search_depth="advanced",
                        max_results=query_spec.depth,
                        include_domains=query_spec.preferred_domains
                    )
                )

            if query_spec.official_source_available:
                search_tasks.append(
                    self.official_api_agent.query(
                        source=query_spec.api_source,
                        endpoint=query_spec.endpoint,
                        params=query_spec.params
                    )
                )

        # Execute in parallel
        results = await asyncio.gather(*search_tasks)

        # Deduplicate and merge
        merged_results = self.deduplicate_results(results)

        return merged_results

    def deduplicate_results(self, results):
        """
        Remove duplicate content from multiple tool results
        """
        seen_urls = set()
        seen_content_hashes = set()
        unique_results = []

        for result in results:
            # URL-based deduplication
            if result.url not in seen_urls:
                # Content-based deduplication (fuzzy matching)
                content_hash = self.hash_content(result.content)

                if content_hash not in seen_content_hashes:
                    unique_results.append(result)
                    seen_urls.add(result.url)
                    seen_content_hashes.add(content_hash)
                else:
                    # Same content from different URL
                    # Merge metadata but don't duplicate
                    existing = self.find_by_hash(unique_results, content_hash)
                    existing.alternative_urls.append(result.url)

        return unique_results
```

### C. Cost Optimization Strategy

```python
class CostOptimizer:
    """
    Minimize API costs while maximizing information quality
    """
    def __init__(self):
        self.tool_costs = {
            'exa': 0.01,       # per search
            'tavily': 0.005,   # per search
            'perplexity': 0.02,# per query
            'official_api': 0.0 # usually free
        }
        self.budget_per_claim = 0.50  # $0.50 max per claim

    def optimize_search_plan(self, search_plan, priority):
        """
        Optimize search execution for cost-effectiveness
        """
        # Always start with free official APIs
        prioritized_plan = []

        # Tier 1: Free official sources
        official_searches = [
            s for s in search_plan
            if s.tool == 'official_api'
        ]
        prioritized_plan.extend(official_searches)

        # Tier 2: Cost-effective broad searches
        if priority >= PRIORITY_MEDIUM:
            tavily_searches = [
                s for s in search_plan
                if s.tool == 'tavily'
            ]
            prioritized_plan.extend(tavily_searches[:2])  # Limit to 2

        # Tier 3: Precision searches for high-priority claims
        if priority >= PRIORITY_HIGH:
            exa_searches = [
                s for s in search_plan
                if s.tool == 'exa'
            ]
            prioritized_plan.extend(exa_searches[:3])  # Limit to 3

        # Calculate projected cost
        projected_cost = sum(
            self.tool_costs.get(s.tool, 0)
            for s in prioritized_plan
        )

        # If over budget, trim low-priority searches
        if projected_cost > self.budget_per_claim:
            prioritized_plan = self.trim_to_budget(
                prioritized_plan,
                self.budget_per_claim
            )

        return prioritized_plan
```

---

## IX. Output Format: Comprehensive Claim Report

### A. Report Structure

```json
{
  "claim": {
    "original_text": "The 2020 US election had the highest voter turnout in history.",
    "claimed_by": "Social media post",
    "claim_date": "2024-11-20",
    "verification_date": "2024-11-27"
  },

  "verdict": {
    "status": "PARTIALLY_TRUE",
    "confidence": 0.92,
    "summary": "The claim is partially true. The 2020 election had the highest absolute vote count in US history (158.4M votes), but not the highest turnout percentage. The 1876 election had 81.8% turnout compared to 2020's 66.8%."
  },

  "sub_claims": [
    {
      "id": "C1",
      "text": "2020 had highest absolute vote count",
      "verdict": "TRUE",
      "confidence": 0.98,
      "evidence_count": 5
    },
    {
      "id": "C2",
      "text": "2020 had highest turnout percentage",
      "verdict": "FALSE",
      "confidence": 0.95,
      "evidence_count": 6
    }
  ],

  "timeline": [
    {
      "date": "1876-11-07",
      "event": "1876 Presidential Election",
      "data": {
        "total_votes": "8.4 million",
        "turnout_percentage": "81.8%"
      },
      "sources": ["US Census Bureau Historical Statistics"],
      "confidence": 0.95
    },
    {
      "date": "2020-11-03",
      "event": "2020 Presidential Election",
      "data": {
        "total_votes": "158.4 million",
        "turnout_percentage": "66.8%"
      },
      "sources": ["US Census Bureau", "Federal Election Commission"],
      "confidence": 0.99
    }
  ],

  "evidence_summary": {
    "total_sources": 12,
    "tier_1_sources": 6,
    "tier_2_sources": 4,
    "tier_3_sources": 2,
    "contradictions_found": 1,
    "contradictions_resolved": 1,
    "knowledge_gaps": 0
  },

  "key_evidence": [
    {
      "source": "US Census Bureau Current Population Survey",
      "tier": 1,
      "url": "https://www.census.gov/data/...",
      "published": "2021-04-29",
      "excerpt": "Approximately 158.4 million people reported voting in the 2020 presidential election, representing 66.8% of the citizen voting-age population.",
      "relevance": "Primary source for 2020 turnout data",
      "supports": ["C1", "C2"]
    },
    {
      "source": "Historical Statistics of the United States",
      "tier": 1,
      "url": "https://www.census.gov/history/...",
      "published": "1975",
      "excerpt": "1876 election turnout: 81.8% of eligible voters",
      "relevance": "Historical comparison baseline",
      "contradicts": ["C2"]
    }
  ],

  "contradictions": [
    {
      "type": "DEFINITIONAL_AMBIGUITY",
      "description": "The term 'highest turnout' can mean either highest percentage or highest absolute number",
      "resolution": "Clarified both metrics in verdict. Claim is true for absolute count, false for percentage.",
      "confidence_impact": -0.05
    }
  ],

  "investigation_metadata": {
    "recursion_depth": 2,
    "total_searches": 8,
    "tools_used": ["tavily", "exa", "official_api"],
    "time_elapsed_seconds": 23.4,
    "cost_usd": 0.12
  },

  "caveats": [
    "Voter eligibility criteria changed significantly over US history (e.g., women's suffrage in 1920, Voting Rights Act of 1965), making direct percentage comparisons complex.",
    "Some historical turnout data relies on estimates rather than exact counts."
  ],

  "recommended_actions": [
    "Share verdict with contextual note about dual metrics",
    "Monitor for similar claims using misleading framing",
    "No further investigation needed - high confidence"
  ]
}
```

### B. Human-Readable Report Format

```markdown
# Fact-Check Report

## Claim

**"The 2020 US election had the highest voter turnout in history."**

_Claimed by:_ Social media post  
_Claim date:_ November 20, 2024  
_Verified on:_ November 27, 2024

---

## Verdict: PARTIALLY TRUE

**Confidence: 92%**

The claim is **partially true**. The 2020 election achieved the highest **absolute vote count** in US history with 158.4 million votes cast. However, it did **not** have the highest **turnout percentage**. The 1876 election holds that record with 81.8% of eligible voters participating, compared to 66.8% in 2020.

The ambiguity stems from how "highest turnout" is defined—by total votes or by percentage of eligible voters.

---

## Timeline of Key Events

**November 7, 1876 - 1876 Presidential Election**

- Total votes: 8.4 million
- Turnout: 81.8% of eligible voters
- _Source: US Census Bureau Historical Statistics (Tier 1)_

**November 3, 2020 - 2020 Presidential Election**

- Total votes: 158.4 million
- Turnout: 66.8% of eligible voters
- _Sources: US Census Bureau, Federal Election Commission (Tier 1)_

---

## Evidence Analysis

**Total Sources Evaluated:** 12

- Tier 1 (Official/Primary): 6 sources
- Tier 2 (Expert/Academic): 4 sources
- Tier 3 (News): 2 sources

**Key Evidence:**

1. **US Census Bureau Current Population Survey** (Tier 1)

   - "Approximately 158.4 million people reported voting in the 2020 presidential election, representing 66.8% of the citizen voting-age population."
   - Published: April 29, 2021

2. **Historical Statistics of the United States** (Tier 1)
   - 1876 election turnout: 81.8% of eligible voters
   - Published: 1975

---

## Important Context

- Voter eligibility has changed dramatically throughout US history:

  - Women gained voting rights in 1920 (19th Amendment)
  - Voting Rights Act of 1965 removed discriminatory barriers
  - 26th Amendment (1971) lowered voting age to 18

- These changes make direct percentage comparisons across eras complex and require contextual understanding.

---

## Investigation Details

- Recursion depth: 2 levels
- Searches performed: 8
- Tools used: Tavily, Exa, Official APIs
- Time: 23.4 seconds
- Contradictions found: 1 (definitional ambiguity)
- Contradictions resolved: 1

---

## Recommendation

This claim can be shared with proper context explaining both metrics. No further investigation needed.
```

---

## X. Implementation Pseudocode

### Complete System Integration

```python
# Main orchestrator implementation
class AdvancedClaimVerificationSystem:
    def __init__(self, config):
        self.config = config

        # Initialize agents
        self.orchestrator = OrchestratorAgent(config)
        self.decomposer = DecomposerAgent()
        self.planner = PlannerAgent()
        self.evaluator = EvaluatorAgent()

        # Initialize tool agents
        self.exa = ExaSearchAgent(config.exa_api_key)
        self.tavily = TavilySearchAgent(config.tavily_api_key)
        self.official_api = OfficialAPIAgent()
        self.forensic = ForensicAnalysisAgent()

        # Initialize support systems
        self.confidence_scorer = ConfidenceScorer()
        self.timeline_builder = TimelineConstructor()
        self.contradiction_resolver = ContradictionResolver()
        self.cost_optimizer = CostOptimizer()

    async def verify_claim(self, claim, priority="HIGH"):
        """
        Main entry point for claim verification
        """
        print(f"Starting verification for: {claim}")

        # Initialize investigation state
        investigation = Investigation(
            claim=claim,
            priority=priority,
            start_time=time.time()
        )

        # STAGE 1: Decompose claim
        print("\n[Stage 1/7] Decomposing claim...")
        sub_claims = await self.decomposer.decompose(claim)
        investigation.add_sub_claims(sub_claims)

        # STAGE 2-3: Plan and execute searches
        print("\n[Stage 2-3/7] Planning and executing searches...")

        for sub_claim in sub_claims:
            # Create search plan
            search_plan = await self.planner.create_plan(
                sub_claim,
                priority=priority
            )

            # Optimize for cost
            optimized_plan = self.cost_optimizer.optimize_search_plan(
                search_plan,
                priority
            )

            # Execute searches in parallel
            evidence = await self.execute_multi_tool_search(
                optimized_plan
            )

            investigation.add_evidence(sub_claim.id, evidence)

        # STAGE 4: Evaluate evidence
        print("\n[Stage 4/7] Evaluating evidence...")
        evaluation = await self.evaluator.assess(
            investigation.evidence_collection
        )
        investigation.set_evaluation(evaluation)

        # RECURSION DECISION POINT
        if self.should_recurse(evaluation, investigation.depth):
            print(f"\n[Recursion] Confidence {evaluation.confidence:.2f} below threshold. Going deeper...")

            # Identify what needs deeper investigation
            deeper_claims = self.identify_recursion_targets(evaluation)

            # Recursive investigations
            for deeper_claim in deeper_claims:
                sub_investigation = await self.verify_claim(
                    deeper_claim,
                    priority=priority
                )
                investigation.merge_sub_investigation(sub_investigation)

            # Re-evaluate with new evidence
            evaluation = await self.evaluator.assess(
                investigation.evidence_collection
            )
            investigation.set_evaluation(evaluation)

        # STAGE 5: Forensic analysis (if needed)
        if self.contains_multimedia(claim):
            print("\n[Stage 5/7] Running forensic analysis...")
            forensic_results = await self.forensic.analyze(claim)
            investigation.add_forensic_evidence(forensic_results)
        else:
            print("\n[Stage 5/7] No multimedia detected, skipping forensics")

        # STAGE 6: Synthesize and resolve contradictions
        print("\n[Stage 6/7] Synthesizing evidence...")

        if evaluation.has_contradictions:
            print(f"  Found {len(evaluation.contradictions)} contradictions, resolving...")
            resolutions = await self.contradiction_resolver.resolve(
                evaluation.contradictions
            )
            investigation.apply_resolutions(resolutions)

        # Build timeline
        timeline = await self.timeline_builder.build(
            investigation.evidence_collection
        )
        investigation.set_timeline(timeline)

        # Calculate final confidence
        final_confidence = self.confidence_scorer.calculate_confidence(
            investigation.evidence_collection,
            claim
        )

        # Determine verdict
        verdict = self.determine_verdict(
            investigation,
            final_confidence
        )
        investigation.set_verdict(verdict, final_confidence)

        # STAGE 7: Format report
        print("\n[Stage 7/7] Formatting comprehensive report...")
        report = self.format_report(investigation)

        print(f"\n✓ Verification complete")
        print(f"  Verdict: {verdict}")
        print(f"  Confidence: {final_confidence:.2%}")
        print(f"  Sources: {len(investigation.evidence_collection)}")
        print(f"  Time: {time.time() - investigation.start_time:.1f}s")

        return report

    async def execute_multi_tool_search(self, search_plan):
        """
        Execute searches across multiple tools in parallel
        """
        tasks = []

        for query in search_plan:
            if query.tool == "exa":
                tasks.append(self.exa.search(query))
            elif query.tool == "tavily":
                tasks.append(self.tavily.search(query))
            elif query.tool == "official_api":
                tasks.append(self.official_api.query(query))

        results = await asyncio.gather(*tasks)

        # Merge and deduplicate
        merged = self.merge_results(results)

        return merged

    def should_recurse(self, evaluation, current_depth):
        """
        Determine if recursion is needed
        """
        if current_depth >= self.config.max_recursion_depth:
            return False

        if evaluation.confidence >= self.config.confidence_threshold:
            return False

        if evaluation.has_contradictions:
            return True

        if evaluation.critical_knowledge_gaps:
            return True

        if evaluation.timeline_conflicts:
            return True

        if evaluation.primary_source_count == 0 and current_depth == 0:
            return True

        return False

    def determine_verdict(self, investigation, confidence):
        """
        Determine final verdict based on evidence
        """
        evidence = investigation.evidence_collection

        # Count verdicts from sources
        verdicts = [e.verdict for e in evidence]

        true_count = verdicts.count("TRUE")
        false_count = verdicts.count("FALSE")
        partial_count = verdicts.count("PARTIAL")

        total = len(verdicts)

        if confidence < 0.4:
            return "UNVERIFIABLE"

        if true_count / total >= 0.8:
            return "TRUE"
        elif false_count / total >= 0.8:
            return "FALSE"
        elif partial_count / total >= 0.5 or \
             (true_count > 0 and false_count > 0):
            return "PARTIALLY_TRUE"
        else:
            return "MIXED_EVIDENCE"

    def format_report(self, investigation):
        """
        Format comprehensive final report
        """
        return {
            "claim": investigation.claim,
            "verdict": {
                "status": investigation.verdict,
                "confidence": investigation.confidence,
                "summary": investigation.generate_summary()
            },
            "sub_claims": investigation.sub_claims,
            "timeline": investigation.timeline,
            "evidence_summary": investigation.get_evidence_summary(),
            "key_evidence": investigation.get_key_evidence(limit=10),
            "contradictions": investigation.resolutions,
            "investigation_metadata": {
                "recursion_depth": investigation.depth,
                "total_searches": investigation.search_count,
                "tools_used": investigation.tools_used,
                "time_elapsed": time.time() - investigation.start_time,
                "cost_usd": investigation.total_cost
            },
            "caveats": investigation.generate_caveats(),
            "recommended_actions": investigation.generate_recommendations()
        }


# Example usage
async def main():
    config = VerificationConfig(
        max_recursion_depth=5,
        confidence_threshold=0.85,
        exa_api_key="...",
        tavily_api_key="..."
    )

    system = AdvancedClaimVerificationSystem(config)

    claim = "President Biden announced a $2 trillion infrastructure plan in March 2021, the largest in US history."

    report = await system.verify_claim(claim, priority="HIGH")

    # Output formatted report
    print(json.dumps(report, indent=2))

    # Or generate human-readable markdown
    markdown_report = system.generate_markdown_report(report)
    print(markdown_report)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## XI. Advanced Features & Extensions

### A. Learning & Adaptation

```python
class AdaptiveLearningModule:
    """
    Learn from past verifications to improve future performance
    """
    def __init__(self):
        self.verification_history = []
        self.source_performance_db = {}

    def record_verification(self, investigation, user_feedback=None):
        """
        Record verification for learning
        """
        record = {
            'claim_type': investigation.claim_type,
            'sources_used': investigation.sources,
            'confidence': investigation.confidence,
            'verdict': investigation.verdict,
            'search_strategies': investigation.search_strategies,
            'recursion_depth': investigation.depth,
            'user_feedback': user_feedback
        }

        self.verification_history.append(record)
        self.update_source_performance(investigation)

    def update_source_performance(self, investigation):
        """
        Track which sources are most reliable over time
        """
        for source in investigation.sources:
            if source.url not in self.source_performance_db:
                self.source_performance_db[source.url] = {
                    'times_used': 0,
                    'times_correct': 0,
                    'average_confidence': 0,
                    'claim_types': set()
                }

            db_entry = self.source_performance_db[source.url]
            db_entry['times_used'] += 1

            # If verdict aligned with final verdict
            if source.verdict == investigation.verdict:
                db_entry['times_correct'] += 1

            db_entry['average_confidence'] = (
                (db_entry['average_confidence'] * (db_entry['times_used'] - 1) +
                 investigation.confidence) / db_entry['times_used']
            )

            db_entry['claim_types'].add(investigation.claim_type)

    def suggest_sources(self, claim_type):
        """
        Suggest best sources based on historical performance
        """
        relevant_sources = [
            (url, data)
            for url, data in self.source_performance_db.items()
            if claim_type in data['claim_types']
        ]

        # Rank by accuracy and confidence
        ranked = sorted(
            relevant_sources,
            key=lambda x: (
                x[1]['times_correct'] / x[1]['times_used'],
                x[1]['average_confidence']
            ),
            reverse=True
        )

        return [url for url, data in ranked[:10]]
```

### B. Real-Time Monitoring & Alert System

```python
class MisinformationMonitor:
    """
    Monitor social media for emerging false claims
    """
    async def monitor_platforms(self, keywords, threshold_shares=1000):
        """
        Track claim propagation in real-time
        """
        while True:
            # Check social media APIs for trending claims
            trending_claims = await self.fetch_trending_claims(keywords)

            for claim in trending_claims:
                # Check if already verified
                if claim.text in self.verified_claims_cache:
                    continue

                # Check virality
                if claim.share_count >= threshold_shares:
                    # Trigger urgent verification
                    report = await self.system.verify_claim(
                        claim.text,
                        priority="URGENT"
                    )

                    # If false, issue alert
                    if report['verdict']['status'] == "FALSE":
                        await self.issue_alert(claim, report)

            await asyncio.sleep(300)  # Check every 5 minutes

    async def issue_alert(self, claim, report):
        """
        Alert relevant parties about viral misinformation
        """
        alert = {
            'claim': claim.text,
            'verdict': report['verdict'],
            'virality': claim.share_count,
            'platforms': claim.platforms,
            'report_url': self.publish_report(report)
        }

        # Notify fact-checking organizations
        await self.notify_partners(alert)

        # Post correction
        await self.post_correction(alert)
```

---

## XII. Best Practices & Recommendations

### A. When to Use Recursive Investigation

**Always Recurse When:**

- Confidence < 0.60
- Contradictions between Tier 1 sources
- Zero primary sources found
- Claim involves comparative statements without baseline
- Timeline has critical gaps
- Multimedia authenticity questioned

**Consider Recursion When:**

- Confidence between 0.60-0.75
- Only Tier 2-3 sources available
- Minor contradictions exist
- Context seems incomplete
- Claim is high-stakes (legal, medical, safety)

**Don't Recurse When:**

- Confidence > 0.85 with Tier 1 sources
- Already at max depth (typically 5)
- Simple factual claim with clear consensus
- Cost exceeds budget constraints

### B. Source Hierarchy Enforcement

```
ALWAYS PRIORITIZE IN THIS ORDER:
1. Official government records/databases
2. Direct organizational statements (when about that organization)
3. Peer-reviewed academic research
4. Established fact-checking organizations
5. Major news organizations with editorial standards
6. Domain experts with verified credentials
7. Secondary analysis with strong citations

NEVER RELY SOLELY ON:
- Social media posts
- Anonymous sources
- Sites with known bias without corroboration
- Outdated sources (>5 years for changing topics)
```

### C. Error Handling & Graceful Degradation

```python
class RobustVerificationSystem(AdvancedClaimVerificationSystem):
    """
    Enhanced system with comprehensive error handling
    """
    async def verify_claim_robust(self, claim, priority="HIGH"):
        try:
            return await self.verify_claim(claim, priority)
        except APIRateLimitError as e:
            # Fallback to cached results or alternative tools
            return await self.verify_with_fallback(claim)
        except InsufficientEvidenceError as e:
            # Return unverifiable verdict with explanation
            return self.create_unverifiable_report(claim, e)
        except ContradictionDeadlockError as e:
            # Return mixed evidence verdict
            return self.create_mixed_evidence_report(claim, e)
        except Exception as e:
            # Log error and return graceful failure
            self.log_error(claim, e)
            return self.create_error_report(claim, e)
```

---

## XIII. Conclusion

This agentic architecture represents a comprehensive, production-ready system for claim verification that:

✅ **Mimics elite journalism** through 7-stage verification workflow  
✅ **Adapts to complexity** via recursive multi-agent investigation  
✅ **Prioritizes quality** through source hierarchy and confidence scoring  
✅ **Provides transparency** with full evidence trails and citations  
✅ **Scales efficiently** through parallel searches and cost optimization  
✅ **Handles multimedia** through integrated forensic tools  
✅ **Constructs timelines** for temporal claim verification  
✅ **Resolves contradictions** systematically  
✅ **Learns and improves** from historical performance

The system balances **thoroughness** (comprehensive investigation) with **adaptability** (context-driven depth), ensuring both accuracy and efficiency in an era of rapid information spread.
