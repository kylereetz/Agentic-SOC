graph LR
    %% Main external components
    subgraph External["External Infrastructure"]
LB[Load Balancer]
API[API Gateway]
Auth[Authentication Layer < br > OAuth2 / JWT]
end

    subgraph Data["Data Tier"]
PrimaryDB[(Primary Database < br > PostgreSQL / MongoDB)]
VectorDB[(Vector Database < br > Pinecone / Milvus)]
Cache[(Cache Layer < br > Redis)]
end

    subgraph Integrations["External Integrations"]
ExternalAPI[Third - party APIs < br > e.g.Threat Intel]
Storage[Cloud Storage < br > S3 / GCS]
end

    subgraph Observability["Observation & Logging"]
Monitor[Monitoring Stack < br > Prometheus / Grafana]
Log[Centralized Logging < br > ELK / Loki]
end

    %% The Extended Agent Pool
    subgraph AgentPool["Agent Pool (Compute Cluster)"]
Queue[[Task Queue < br > RabbitMQ / Redis]]
Scaling[Scaling Manager]

        subgraph Core_Orchestration["Core Orchestration"]
A_Manager[1. SENTINEL - MANAGER]
A_Orches[2. SENTINEL - ORCHESTRATOR]
end

        subgraph Detection_Intel["Detection & Intelligence"]
A_Triage[3. SENTINEL - TRIAGE]
A_Corre[4. SENTINEL - CORRELATOR]
A_Lib[5. SENTINEL - LIBRARIAN POOL]
A_Hunter[6. SENTINEL - HUNTER]
A_Log[7. SENTINEL - LOG - GUARDIAN]
A_Traffic[8. SENTINEL - TRAFFIC - SIEVE]
A_Endpt[9. SENTINEL - ENDPOINT - ANALYST]
A_Hist[24. SENTINEL - HISTORIAN]
end

        subgraph Investigate_Eng["Investigation & Engineering"]
A_Invest[10. SENTINEL - INVESTIGATOR]
A_Foren[11. SENTINEL - FORENSICS]
A_Malw[12. SENTINEL - MALWARE - PATHOLOGIST]
A_Topo[20. SENTINEL - TOPOLOGY]
end

        subgraph Response_Ops["Response & Operations"]
A_Resp[14. SENTINEL - RESPONDER]
A_Patch[15. SENTINEL - PATCHPILOT]
A_Gate[16. SENTINEL - GATEKEEPER]
A_Van[17. SENTINEL - VANGUARD]
A_Mir[18. SENTINEL - MIRAGE]
A_Scout[19. SENTINEL - SCOUT]
end

        subgraph Business_Gov["Business & Governance"]
A_Gov[20. SENTINEL - GOVERNOR]
A_Comm[21. SENTINEL - COMMUNICATOR]
A_Watch[22. SENTINEL - WATCHDOG]
A_Red[23. SENTINEL - RED]
A_Strat[26. SENTINEL - STRATEGIST]
end
end

    %% Ingress Flow
LB -->| HTTPS | API
API <-->| REST / gRPC | Auth
API -->| REST / WebSockets | A_Orches

    %% Core Orchestration & Queuing
A_Orches <-->| gRPC Sync | A_Manager
A_Orches -->| AMQP / PubSub | Queue
A_Orches -->| gRPC Provisioning | Scaling

    %% Task Dispatches & True Topic Queues
    Queue ==>| Raw Events | A_Triage
    A_Triage ==>| publishes to triage_alerts | Queue
    
    Queue ==>| pops from triage_alerts | A_Orches
    A_Orches ==>| publishes to target topic_* | Queue
    
    %% Independent Worker Polling
    Queue -.->| topic_network / topic_ot | A_Endpt & A_Traffic & A_Invest
    Queue -.->| topic_identity | A_Foren
    Queue -.->| topic_malware | A_Malw & A_Hunter
    Queue -.->| topic_remediation | A_Resp & A_Patch
    
    %% Hive Consensus Callbacks
    A_Endpt & A_Malw & A_Hunter & A_Invest -.->| publishes to orchestrator_callbacks | Queue
    Queue -.->| monitors orchestrator_callbacks | A_Orches

    %% Service Mesh Data Tier Interactions (Zero Trust)
A_Manager -->| mTLS / SQL | PrimaryDB
A_Orches -->| mTLS / SQL | PrimaryDB
Queue -->| mTLS / State Backup | Cache
A_Manager -->| mTLS / Redis Protocol | Cache

    %% Vector / RAG Connections (Librarian heavily mediates this)
A_Lib <-->| mTLS / gRPC | VectorDB
A_Invest -.->| mTLS Query | A_Lib
A_Hunter -.->| mTLS Query | A_Lib

    %% Specific External Integrations
A_Triage -->| REST APIs | ExternalAPI
A_Van -->| SBOM Ingestion | ExternalAPI
A_Comm -->| SMTP / Webhook | ExternalAPI
A_Foren -->| HTTPS Strict IAM Role | Storage

    %% Dedicated Observability Interactions
A_Watch -->| Scrape Node / PromQL | Monitor
A_Watch -.->| Heartbeat Ping | Scaling
Scaling -->| Worker Metrics | Monitor
A_Red -.->| Injects Synthetic Threats on discovery_events | Queue

A_Log -->| Norm.JSON Push | Log
A_Manager -.->| Audit Trails | Log
A_Orches -.->| Syslog | Log
