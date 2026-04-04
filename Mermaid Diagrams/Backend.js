graph LR
    %% Subgraphs mapping logical sections
    subgraph External["External Infrastructure"]
LB[Load Balancer]
API[API Gateway]
Auth[Authentication Layer < br > OAuth2 / JWT]
end

    subgraph Compute["Compute Cluster (Agent Pool)"]
Orchestrator[Orchestrator]
Scaling[Scaling Manager]
Queue[[Task Queue < br > RabbitMQ / Redis]]
Workers[Task - specific Worker Agents < br > e.g., Scout, Triage, Investigator]
end

    subgraph Data["Data Tier"]
PrimaryDB[(Primary Database < br > PostgreSQL / MongoDB)]
VectorDB[(Vector Database < br > Pinecone / Milvus)]
Cache[(Cache Layer < br > Redis)]
end

    subgraph Integrations["External Integrations"]
ExternalAPI[Third - party APIs]
Storage[Cloud Storage < br > S3 / GCS]
end

    subgraph Observability["Observation & Logging"]
Monitor[Monitoring Stack < br > Prometheus / Grafana]
Log[Centralized Logging < br > ELK / Loki]
end

    %% Ingress and Gateway Flow
LB-- >| HTTPS | API
API < -->| REST / gRPC | Auth
API-- >| REST / WebSockets | Orchestrator

    %% Topic - Based Routing & Agent Execution Dynamics
Orchestrator-- >| gRPC / REST API | Scaling
Scaling-- >| Control Plane Metrics | Workers
Orchestrator-- >| AMQP Topic Exchange(e.g.topic_cloud) | Queue
Queue -.->| Subscribed Topic Consumption | Workers
Workers -.->| Hive Consensus Callbacks(orchestrator_callbacks) | Queue
Queue -.->| Consensus Monitor Loop | Orchestrator

    %% Service Mesh Data Tier Connections(Zero Trust)
Orchestrator-- >| mTLS / SQL | PrimaryDB
Workers-- >| mTLS / SQL | PrimaryDB
Workers -.->| mTLS RAG Query | LibrarianCluster[Librarian Cluster]
LibrarianCluster-- >| mTLS / gRPC | VectorDB
Workers-- >| mTLS / Redis RESP | Cache
Orchestrator-- >| mTLS / Redis RESP | Cache

    %% External Systems Interfacing
Workers-- >| HTTPS / REST | ExternalAPI
Workers-- >| HTTPS(Strict IAM Role) | Storage
Orchestrator-- >| HTTPS(Strict IAM Role) | Storage

    %% Telemetry, Observability & Logging(Dotted lines for non - blocking flows)
    API -.->| HTTP / UDP | Log
Orchestrator -.->| HTTP / UDP | Log
Workers -.->| HTTP / UDP | Log
Queue -.->| HTTP / UDP | Log

Orchestrator -.->| Prometheus Scrape / HTTP | Monitor
Workers -.->| Prometheus Scrape / HTTP | Monitor
Scaling -.->| Prometheus Scrape | Monitor
PrimaryDB -.->| Prometheus Scrape | Monitor
