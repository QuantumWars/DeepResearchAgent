# System Architecture Diagram

## Overall System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[User/main.py]
    end

    subgraph "Orchestration Layer"
        ORC[OrchestratorAgent]
        ORC --> |Recursion Control| ORC
    end

    subgraph "Agent Layer"
        DEC[DecomposerAgent<br/>GPT-4o]
        PLAN[PlannerAgent<br/>Strategy]
        EVAL[EvaluatorAgent<br/>Assessment]
        FOR[ForensicAgent<br/>Multimedia]
    end

    subgraph "Core Logic Layer"
        CONF[ConfidenceScorer]
        TIME[TimelineConstructor]
        CONT[ContradictionResolver]
        COST[CostOptimizer]
    end

    subgraph "Tool Layer"
        EXA[Exa Search<br/>Semantic]
        TAV[Tavily Search<br/>Web/News]
        OFF[Official APIs<br/>.gov]
    end

    subgraph "Data Layer"
        MODELS[Pydantic Schemas<br/>Claim, Evidence, Verdict]
    end

    UI --> ORC
    ORC --> DEC
    ORC --> PLAN
    ORC --> EVAL
    ORC --> FOR
    ORC --> CONF
    ORC --> TIME
    ORC --> CONT
    ORC --> COST
    PLAN --> EXA
    PLAN --> TAV
    PLAN --> OFF
    ORC --> MODELS

    style ORC fill:#ff6b6b
    style DEC fill:#4ecdc4
    style EXA fill:#95e1d3
    style TAV fill:#95e1d3
    style CONF fill:#ffe66d
```

## Verification Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant D as Decomposer
    participant S as SearchTools
    participant C as ConfidenceScorer

    U->>O: Submit Claim
    O->>D: Decompose claim
    D->>D: GPT-4o Analysis
    D-->>O: Sub-claims JSON

    loop For each sub-claim
        O->>S: Execute searches
        S->>S: Exa + Tavily APIs
        S-->>O: Evidence list
    end

    O->>C: Calculate confidence
    C-->>O: Confidence score

    alt Confidence < 70%
        O->>O: Recursive investigation (depth+1)
        O->>S: Additional searches
        S-->>O: More evidence
        O->>C: Re-calculate
    end

    O-->>U: Investigation Result
```

## Recursion Decision Flow

```mermaid
flowchart TD
    START([Start Verification]) --> DECOMP[Decompose Claim]
    DECOMP --> SEARCH[Execute Searches]
    SEARCH --> EVIDENCE[Gather Evidence]
    EVIDENCE --> EVAL[Evaluate & Calculate Confidence]

    EVAL --> DECISION{Should Recurse?}

    DECISION -->|Confidence >= 85%| SKIP[Skip Recursion]
    DECISION -->|Depth >= Max| SKIP
    DECISION -->|Confidence < 70%| RECURSE[Trigger Recursion]
    DECISION -->|Has Contradictions| RECURSE
    DECISION -->|No Primary Sources| RECURSE

    RECURSE --> GAPS[Identify Knowledge Gaps]
    GAPS --> GEN[Generate Follow-up Claims]
    GEN --> REC_CALL[Recursive verify_claim<br/>Depth + 1]
    REC_CALL --> MERGE[Merge Evidence]
    MERGE --> RECALC[Re-calculate Confidence]

    SKIP --> SYNTH[Synthesize Results]
    RECALC --> SYNTH
    SYNTH --> REPORT[Generate Report]
    REPORT --> END([Return Result])

    style DECISION fill:#ff6b6b
    style RECURSE fill:#ffd93d
    style SKIP fill:#6bcf7f
```

## Data Flow

```mermaid
graph LR
    subgraph Input
        CLAIM[Original Claim]
    end

    subgraph Processing
        SC[Sub-Claims]
        SP[Search Plan]
        EV[Evidence Collection]
        CF[Confidence Score]
    end

    subgraph Output
        VER[Verdict]
        REP[Investigation Report]
    end

    CLAIM --> SC
    SC --> SP
    SP --> EV
    EV --> CF
    CF --> VER
    VER --> REP

    EV -.->|If Low Confidence| SC

    style CLAIM fill:#e3f2fd
    style REP fill:#c8e6c9
    style CF fill:#fff9c4
```

## Source Tier Classification

```mermaid
graph TD
    SOURCE[Source URL] --> CHECK{Domain Check}

    CHECK -->|.gov, .edu| T1[Tier 1<br/>Official/Academic<br/>Weight: 1.0]
    CHECK -->|factcheck.org,<br/>politifact.com| T2[Tier 2<br/>Fact-Checkers<br/>Weight: 0.85]
    CHECK -->|nytimes.com,<br/>bbc.com| T3[Tier 3<br/>Major News<br/>Weight: 0.70]
    CHECK -->|Other| T4[Tier 4<br/>General Sources<br/>Weight: 0.50]

    style T1 fill:#4caf50
    style T2 fill:#8bc34a
    style T3 fill:#ffc107
    style T4 fill:#ff9800
```

## Confidence Calculation

```mermaid
graph LR
    subgraph Factors
        SQ[Source Quality 30%]
        SA[Source Agreement 25%]
        SD[Source Diversity 15%]
        TC[Temporal Consistency 10%]
        LC[Logical Coherence 10%]
        PS[Primary Sources 10%]
    end

    subgraph Penalties
        CON[Contradictions -20%]
        SS[Single Source -15%]
        NPS[No Primary -10%]
    end

    SQ --> SUM[Weighted Sum]
    SA --> SUM
    SD --> SUM
    TC --> SUM
    LC --> SUM
    PS --> SUM

    SUM --> APPLY[Apply Penalties]
    CON --> APPLY
    SS --> APPLY
    NPS --> APPLY

    APPLY --> FINAL[Final Confidence<br/>0.0 - 1.0]

    style SUM fill:#fff9c4
    style APPLY fill:#ffccbc
    style FINAL fill:#c8e6c9
```

## Component Interaction Matrix

```
┌─────────────────┬──────────┬──────────┬──────────┬──────────┐
│                 │ Decomp   │ Planner  │ Evaluator│ Forensic │
├─────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Orchestrator    │    ✓     │    ✓     │    ✓     │    ✓     │
│ SearchTools     │    ✗     │    ✓     │    ✗     │    ✗     │
│ ConfidenceScorer│    ✗     │    ✗     │    ✓     │    ✗     │
│ TimelineBuilder │    ✗     │    ✗     │    ✓     │    ✗     │
│ CostOptimizer   │    ✗     │    ✓     │    ✗     │    ✗     │
└─────────────────┴──────────┴──────────┴──────────┴──────────┘

Legend: ✓ = Direct interaction, ✗ = No direct interaction
```
