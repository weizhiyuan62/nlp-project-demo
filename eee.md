```Mermaid
flowchart TB
    %% =========================
    %% Data Sources
    %% =========================
    subgraph S1["Multi-source Information Acquisition"]
        A1["SerpAPI<br/>(Google Search)"]
        A2["NewsAPI"]
        A3["arXiv API"]
    end

    %% =========================
    %% Data Collection Layer
    %% =========================
    subgraph S2["Unified Data Collection Layer"]
        B["Data Collector<br/>(Configurable Crawling)"]
    end

    %% =========================
    %% LLM Judging Layer
    %% =========================
    subgraph S3["LLM-based Quality Assessment"]
        C["LLM Analyzer (Qwen API)<br/>• Multi-threading<br/>• Batch Scoring<br/>• Multi-dimensional Evaluation"]
        C1["Relevance"]
        C2["Importance"]
        C3["Timeliness"]
        C4["Reliability"]
    end

    %% =========================
    %% Analysis & Visualization
    %% =========================
    subgraph S4["Statistical Analysis & Visualization"]
        D1["Word Cloud"]
        D2["Temporal Trend"]
        D3["Source Distribution"]
    end

    %% =========================
    %% Report Generation
    %% =========================
    subgraph S5["Automated Report Generation"]
        E1["Report Generator<br/>(Markdown)"]
        E2["LaTeX Compiler"]
    end

    %% =========================
    %% Final Output
    %% =========================
    F["Final Output<br/>Structured Reports (PDF + Markdown)"]

    %% =========================
    %% Flow
    %% =========================
    A1 --> B
    A2 --> B
    A3 --> B

    B --> C

    C --> C1
    C --> C2
    C --> C3
    C --> C4

    C --> D1
    C --> D2
    C --> D3

    D1 --> E1
    D2 --> E1
    D3 --> E1

    E1 --> E2
    E2 --> F
```