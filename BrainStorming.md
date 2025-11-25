## System Overview: 3-Tier Hierarchical Structure

```
┌─────────────────────────────────────────────────┐
│     ORCHESTRATION LAYER (Supervisor)            │
│  - Claim decomposition & routing                │
│  - Global context management                    │
│  - Confidence aggregation & HITL decisions      │
└─────────────────────────────────────────────────┘
                      ↓↑
┌─────────────────────────────────────────────────┐
│     SPECIALIST WORKER AGENTS (8 Agents)         │
│  - Domain experts (Political, Scientific, etc)  │
│  - Source verification specialist               │
│  - Evidence synthesis coordinator               │
└─────────────────────────────────────────────────┘
                      ↓↑
┌─────────────────────────────────────────────────┐
│     TOOL LAYER (Utilities & APIs)               │
│  - Search, databases, analysis tools            │
│  - Credibility scoring APIs                     │
│  - Memory systems                               │
└─────────────────────────────────────────────────┘
```

## Core Agent Roster

### 1. **Supervisor Orchestrator Agent**

- **Role**: Decomposes claims, routes to specialists, aggregates findings, makes HITL decisions
- **Capabilities**:
    - Parse complex claims into atomic verifiable statements
    - Identify domain types (political, scientific, statistical, etc)
    - Route to appropriate specialist agents
    - Maintain global investigation state
    - Calculate system-level confidence
    - Trigger human escalation based on rules
- **Memory**: Access to all shared memory layers
- **Tools**: Agent registry, routing logic, confidence aggregator

### 2. **Political Claims Specialist**

- **Expertise**: Government statements, policy claims, voting records, campaign promises
- **Tools**: Congressional Record, FEC data, GovTrack, official government APIs
- **Red Flags**: Cherry-picked timeframes, context removal, partisan source over-reliance
- **Output**: Verdict + confidence + evidence list + reasoning chain

### 3. **Scientific/Medical Claims Specialist**

- **Expertise**: Research papers, medical claims, health information
- **Tools**: PubMed API, peer-review databases, Retraction Watch, study quality algorithms
- **Red Flags**: Single study as proof, preprints without flagging, correlation→causation
- **Output**: Evidence hierarchy assessment + expert consensus + uncertainty factors

### 4. **Statistical Claims Specialist**

- **Expertise**: Numerical data, charts, economic statistics, data analysis
- **Tools**: Census API, BLS, FRED, statistical analysis libraries, cherry-picking detectors
- **Red Flags**: Truncated axes, mixing rates/counts, arbitrary timeframes, p-hacking
- **Output**: Data provenance + methodology assessment + context evaluation

### 5. **Visual Content Specialist**

- **Expertise**: Images, videos, deepfakes, manipulated media
- **Tools**: Reverse image search, InVID/WeVerify, metadata extractors, forensic analysis
- **Red Flags**: ELA anomalies, geolocation mismatches, temporal impossibilities
- **Output**: Authenticity score + provenance chain + manipulation indicators

### 6. **Social Media Specialist**

- **Expertise**: Viral content, bot detection, coordinated campaigns
- **Tools**: Bot Sentinel, CrowdTangle, Hoaxy, network analysis, EXIF readers
- **Red Flags**: Coordinated behavior, stolen profiles, identical posting patterns
- **Output**: Virality analysis + bot probability + original source verification

### 7. **Financial/Economic Specialist**

- **Expertise**: Corporate claims, earnings, market data, economic indicators
- **Tools**: SEC EDGAR, XBRL parsers, real-time filing alerts, regulatory databases
- **Red Flags**: Pump-and-dump patterns, fake filings, timing near earnings, anonymous sources
- **Output**: Filing verification + timing analysis + regulatory cross-check

### 8. **Historical/Legal Specialist**

- **Expertise**: Historical facts, legal claims, court records
- **Tools**: National Archives, PACER, CourtListener, historical newspaper databases
- **Red Flags**: Allegations as facts, cherry-picked sources, quote mining from opinions
- **Output**: Source criticism (external + internal) + legal status clarification

### 9. **Source Verification Agent** (Cross-cutting)

- **Role**: Assess credibility of ALL sources used by specialists
- **Scoring**: 4-tier classification (Highly Reliable → High Risk)
- **Signals**: Domain authority, author credentials, content analysis, social signals, propagation
- **Output**: Credibility score + tier classification + confidence modifier

### 10. **Evidence Synthesis Coordinator**

- **Role**: Aggregate findings from all specialists, resolve conflicts, build evidence graph
- **Methods**: Weighted voting, Bayesian updating, Dempster-Shafer for uncertainty
- **Output**: Unified verdict + confidence + evidence relationships + minority views

## Orchestration Workflow

```python
# Pseudocode for main verification pipeline

async def verify_claim(claim: str) -> VerificationReport:
    
    # STAGE 1: Decomposition & Planning
    supervisor = SupervisorAgent()
    sub_claims = supervisor.decompose_claim(claim)
    domains = supervisor.classify_domains(sub_claims)
    plan = supervisor.create_investigation_plan(sub_claims, domains)
    
    # STAGE 2: Parallel Evidence Gathering
    specialist_agents = supervisor.route_to_specialists(domains)
    evidence_tasks = [
        agent.gather_evidence(sub_claim) 
        for agent, sub_claim in zip(specialist_agents, sub_claims)
    ]
    raw_evidence = await asyncio.gather(*evidence_tasks)
    
    # STAGE 3: Source Verification (parallel)
    source_verifier = SourceVerificationAgent()
    credibility_tasks = [
        source_verifier.assess_source(source)
        for evidence in raw_evidence
        for source in evidence.sources
    ]
    credibility_scores = await asyncio.gather(*credibility_tasks)
    
    # STAGE 4: Evidence Synthesis
    synthesizer = EvidenceSynthesisCoordinator()
    weighted_evidence = synthesizer.apply_credibility_weights(
        raw_evidence, credibility_scores
    )
    conflicts = synthesizer.detect_conflicts(weighted_evidence)
    
    if conflicts.high_quality_disagreement:
        # Trigger iterative consensus ensemble
        consensus = await run_ice_protocol(
            specialist_agents, weighted_evidence, rounds=3
        )
        final_verdict = consensus.verdict
        confidence = consensus.confidence
    else:
        final_verdict = synthesizer.aggregate_verdict(weighted_evidence)
        confidence = synthesizer.calculate_confidence(weighted_evidence)
    
    # STAGE 5: Decision Gate
    report = VerificationReport(
        verdict=final_verdict,
        confidence=confidence,
        evidence=weighted_evidence,
        reasoning=synthesizer.reasoning_chain,
        conflicts=conflicts
    )
    
    if supervisor.needs_human_review(report):
        report.status = "PENDING_REVIEW"
        await queue_for_human(report)
    else:
        report.status = "AUTO_VERIFIED"
        await publish_with_sampling(report)
    
    return report
```

## Memory Architecture

### Working Memory (In-Context)

```python
class WorkingMemory:
    current_claim: Claim
    active_sub_claims: List[SubClaim]
    recent_evidence: List[Evidence]  # Last 50 items
    active_reasoning: ReasoningChain
    tool_results: List[ToolResult]  # Last 20 calls
    
    max_tokens: int = 100000  # Context window
```

### Episodic Memory (Investigation History)

```python
class EpisodicMemory:
    storage: VectorDatabase  # Pinecone/ChromaDB
    
    def store_investigation(self, claim, findings, verdict):
        embedding = embed(claim + findings)
        self.storage.upsert(embedding, metadata={
            'claim': claim,
            'verdict': verdict,
            'confidence': confidence,
            'date': timestamp,
            'evidence_summary': summary
        })
    
    def retrieve_similar(self, claim, top_k=5):
        # Find similar past verifications
        return self.storage.query(embed(claim), top_k)
```

### Semantic Memory (Knowledge Base)

```python
class SemanticMemory:
    source_credibility_db: Dict[str, CredibilityScore]
    verified_facts_db: Dict[str, VerifiedFact]
    logical_fallacies: List[FallacyPattern]
    domain_heuristics: Dict[str, DomainRules]
    
    def update_source_credibility(self, source, accuracy):
        # Bayesian update of source reliability
        pass
```

### Procedural Memory (Workflows)

```python
class ProceduralMemory:
    verification_templates: Dict[str, WorkflowTemplate]
    domain_checklists: Dict[str, List[str]]
    escalation_rules: List[EscalationRule]
```

## Tool Ecosystem

### Search & Retrieval

- Web search: Brave API, Google Custom Search
- Academic: PubMed API, Semantic Scholar
- Fact-check DB: ClaimReview schema aggregator
- News archives: NewsAPI, GDELT

### Specialized Databases

- Political: GovTrack API, OpenSecrets, Congressional Record
- Scientific: PubMed, Retraction Watch, ClinicalTrials.gov
- Statistical: Census API, BLS, FRED, World Bank
- Financial: SEC EDGAR, XBRL parsers
- Legal: PACER API, CourtListener
- Historical: National Archives API, Chronicling America

### Analysis Tools

- NLP: NER, sentiment analysis, claim detection
- Statistics: Pandas, NumPy for data validation
- Visual: Reverse image search APIs, forensic analyzers
- Network: Bot detection, propagation analysis

### Credibility Assessment

- Domain authority checkers
- Author credential verifiers
- Content quality analyzers
- Social signal aggregators

## Confidence Scoring System

```python
class ConfidenceCalculator:
    
    def calculate_multilevel_confidence(self, evidence_list):
        
        # Level 1: Evidence-level confidence
        evidence_scores = [
            self.score_evidence(e) for e in evidence_list
        ]
        
        # Level 2: Claim-level confidence
        claim_confidence = self.aggregate_evidence_confidence(
            evidence_scores,
            weights=credibility_weights
        )
        
        # Level 3: System-level calibration
        calibrated = self.apply_calibration(
            claim_confidence,
            temperature=learned_temperature
        )
        
        return ConfidenceScore(
            raw=claim_confidence,
            calibrated=calibrated,
            uncertainty_factors=self.identify_uncertainty(),
            should_escalate=calibrated < 0.60
        )
    
    def score_evidence(self, evidence):
        source_tier = evidence.source.tier  # 1-4
        recency = evidence.age_penalty
        relevance = evidence.relevance_score
        consensus = evidence.corroboration_count
        
        base_score = {1: 0.9, 2: 0.7, 3: 0.5, 4: 0.2}[source_tier]
        return base_score * recency * relevance * sqrt(consensus)
```

## Human-in-the-Loop Integration

### Escalation Rules

```python
class HITLGateway:
    
    def should_escalate(self, report: VerificationReport) -> bool:
        return any([
            report.confidence < 0.60,  # Low confidence
            report.is_high_stakes,  # Health/safety/legal
            report.conflicts.high_quality_disagreement,
            report.is_novel_pattern,
            report.detected_manipulation,
            report.user_requested_review
        ])
    
    def route_review(self, report):
        if report.confidence > 0.80:
            # Random sampling for QA
            if random() < 0.10:
                return ReviewQueue.QA_SAMPLE
        elif report.confidence > 0.60:
            return ReviewQueue.STANDARD
        else:
            return ReviewQueue.PRIORITY
```

### Reviewer Interface Requirements

- Show complete reasoning chain
- Display evidence with credibility scores
- Highlight conflicts and uncertainties
- Allow verdict override with justification
- Capture corrections for retraining

---
