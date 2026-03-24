import type { AnalysisResult, Ticket } from "@/types/ops-decision-engine";

export const mockTickets: Ticket[] = [
  {
    id: "INC-10482",
    title: "SSO login failures for EU finance users",
    issue_description:
      "Users in the EU finance tenant receive intermittent SAML assertion errors during sign-in after identity provider metadata refresh.",
    type: "Incident",
    queue: "IAM Platform",
    timestamp: "2026-03-24T09:12:00Z",
    status: "Open",
    category: "authentication",
  },
  {
    id: "INC-10483",
    title: "Duplicate invoice generation in monthly close",
    issue_description:
      "Billing service generated duplicate invoices for 218 enterprise accounts during month-end job execution window.",
    type: "Problem",
    queue: "Billing Operations",
    timestamp: "2026-03-24T08:50:00Z",
    status: "Investigating",
    category: "billing",
  },
  {
    id: "INC-10484",
    title: "Checkout API p95 latency above SLA",
    issue_description:
      "Checkout endpoint p95 increased from 380ms to 2.1s across APAC region after traffic surge and cache miss spike.",
    type: "Incident",
    queue: "Core API",
    timestamp: "2026-03-24T08:31:00Z",
    status: "Open",
    category: "latency",
  },
  {
    id: "INC-10485",
    title: "500 errors on customer profile update endpoint",
    issue_description:
      "POST /v1/customer/profile returns HTTP 500 for requests including nested preference payloads from mobile clients.",
    type: "Incident",
    queue: "Customer API",
    timestamp: "2026-03-24T07:58:00Z",
    status: "Investigating",
    category: "API errors",
  },
  {
    id: "INC-10486",
    title: "Regional outage impacting US-East tenant traffic",
    issue_description:
      "Ingress controllers in US-East became unhealthy, causing elevated failure rates and routing instability for enterprise tenants.",
    type: "Major Incident",
    queue: "Site Reliability",
    timestamp: "2026-03-24T07:41:00Z",
    status: "Escalated",
    category: "outages",
  },
  {
    id: "INC-10487",
    title: "Admin role assignment not propagating",
    issue_description:
      "Role changes applied in admin console do not appear in downstream policy engine for up to 45 minutes.",
    type: "Incident",
    queue: "Access Governance",
    timestamp: "2026-03-24T07:26:00Z",
    status: "Open",
    category: "access control",
  },
  {
    id: "INC-10488",
    title: "Read replica lag causing stale analytics",
    issue_description:
      "Reporting dashboards show stale usage metrics due to PostgreSQL read replica lag exceeding 12 minutes.",
    type: "Problem",
    queue: "Database Reliability",
    timestamp: "2026-03-24T07:04:00Z",
    status: "Mitigating",
    category: "database issues",
  },
  {
    id: "INC-10489",
    title: "Unusual burst of privileged token requests",
    issue_description:
      "Security monitoring detected a sharp increase in privileged token minting attempts from unknown IP ranges.",
    type: "Security Incident",
    queue: "Security Operations",
    timestamp: "2026-03-24T06:55:00Z",
    status: "Escalated",
    category: "security alerts",
  },
  {
    id: "INC-10490",
    title: "Feature flag misconfiguration after release",
    issue_description:
      "New release enabled an internal-only workflow flag for all production tenants due to incorrect environment targeting.",
    type: "Incident",
    queue: "Release Engineering",
    timestamp: "2026-03-24T06:38:00Z",
    status: "Open",
    category: "deployment/configuration",
  },
  {
    id: "INC-10491",
    title: "Password reset emails delayed beyond 20 minutes",
    issue_description:
      "Transactional email pipeline shows queue backlog and delayed processing for password reset notifications.",
    type: "Incident",
    queue: "Messaging Platform",
    timestamp: "2026-03-24T06:19:00Z",
    status: "Investigating",
    category: "email delivery",
  },
  {
    id: "INC-10492",
    title: "OAuth callback mismatch for newly onboarded tenant",
    issue_description:
      "OAuth redirect URI mismatch blocks login completion for a newly provisioned enterprise tenant instance.",
    type: "Service Request",
    queue: "IAM Platform",
    timestamp: "2026-03-24T05:52:00Z",
    status: "Open",
    category: "authentication",
  },
  {
    id: "INC-10493",
    title: "Charge reconciliation report missing line items",
    issue_description:
      "Nightly reconciliation report omitted usage line items for metered API billing in three high-volume accounts.",
    type: "Problem",
    queue: "Billing Operations",
    timestamp: "2026-03-24T05:27:00Z",
    status: "Open",
    category: "billing",
  },
];

type CategoryDefaults = {
  mlPriority: string;
  recommendedPriority: string;
  confidenceScore: number;
  confidenceLabel: AnalysisResult["confidence_label"];
  escalationDecision: string;
  rootCause: string;
  priorityReasoning: string;
  actionPlan: string[];
  diagnosticSteps: string[];
};

const categoryDefaults: Record<string, CategoryDefaults> = {
  authentication: {
    mlPriority: "P2",
    recommendedPriority: "P2",
    confidenceScore: 0.86,
    confidenceLabel: "High",
    escalationDecision: "Escalate to IAM on-call if failure rate exceeds 15% for 10 minutes.",
    rootCause: "Identity provider metadata or callback configuration mismatch.",
    priorityReasoning:
      "Authentication failures block user access and can rapidly expand blast radius across tenant teams.",
    actionPlan: [
      "Validate identity provider metadata signatures and certificate expiration.",
      "Compare redirect URI and audience values against tenant configuration.",
      "Deploy temporary login fallback route for critical users.",
    ],
    diagnosticSteps: [
      "Review authentication gateway error logs for assertion failures.",
      "Correlate failed requests by tenant and region.",
      "Confirm recent IAM configuration changes in release history.",
    ],
  },
  billing: {
    mlPriority: "P2",
    recommendedPriority: "P2",
    confidenceScore: 0.79,
    confidenceLabel: "Medium",
    escalationDecision: "Escalate to finance systems owner if affected accounts exceed 100.",
    rootCause: "Batch job sequencing defect during monthly billing pipeline execution.",
    priorityReasoning:
      "Billing inaccuracies affect revenue trust and can generate contractual escalations from enterprise customers.",
    actionPlan: [
      "Pause downstream invoice dispatch until reconciliation completes.",
      "Run duplicate detection job across impacted account set.",
      "Prepare customer-facing communication with expected remediation time.",
    ],
    diagnosticSteps: [
      "Inspect batch scheduler timeline for overlapping executions.",
      "Validate idempotency keys in invoice write operations.",
      "Cross-check invoice totals against event ingestion logs.",
    ],
  },
  latency: {
    mlPriority: "P1",
    recommendedPriority: "P1",
    confidenceScore: 0.84,
    confidenceLabel: "High",
    escalationDecision: "Escalate to SRE if p95 remains over 1.5s for 15 minutes.",
    rootCause: "Cache churn combined with elevated upstream dependency latency.",
    priorityReasoning:
      "Sustained latency degradation impacts transaction completion and user experience at scale.",
    actionPlan: [
      "Enable temporary traffic shaping for non-critical endpoints.",
      "Increase cache TTL for high-frequency read paths.",
      "Scale API worker pool in impacted regions.",
    ],
    diagnosticSteps: [
      "Review endpoint-level latency histograms by region.",
      "Check cache hit ratio and eviction rates over last hour.",
      "Trace dependency call durations for checkout pipeline.",
    ],
  },
  "API errors": {
    mlPriority: "P1",
    recommendedPriority: "P1",
    confidenceScore: 0.82,
    confidenceLabel: "High",
    escalationDecision: "Escalate immediately if error rate exceeds 8% on customer-facing endpoints.",
    rootCause: "Unhandled payload variant causing schema validation crash in service layer.",
    priorityReasoning:
      "Elevated 500 responses directly break key user workflows and indicate unsafe backend behavior.",
    actionPlan: [
      "Deploy validation guard for nested preference payload.",
      "Rollback latest serializer patch if regression confirmed.",
      "Enable temporary feature gate for affected client versions.",
    ],
    diagnosticSteps: [
      "Inspect stack traces for recurring exception signatures.",
      "Reproduce failures with captured payload fixtures.",
      "Compare request contracts against deployed API schema.",
    ],
  },
  outages: {
    mlPriority: "P0",
    recommendedPriority: "P0",
    confidenceScore: 0.93,
    confidenceLabel: "High",
    escalationDecision: "Declare major incident and engage incident commander.",
    rootCause: "Regional infrastructure failure affecting ingress and service routing.",
    priorityReasoning:
      "Multi-tenant availability impact requires immediate coordinated response and executive visibility.",
    actionPlan: [
      "Fail over traffic to healthy regions with capacity verification.",
      "Open incident bridge and assign command roles.",
      "Issue external status-page update with mitigation ETA.",
    ],
    diagnosticSteps: [
      "Review ingress controller health and restart events.",
      "Check cloud provider regional incident advisories.",
      "Validate DNS and load balancer failover behavior.",
    ],
  },
  "access control": {
    mlPriority: "P2",
    recommendedPriority: "P2",
    confidenceScore: 0.77,
    confidenceLabel: "Medium",
    escalationDecision: "Escalate to policy platform team if propagation delay exceeds 30 minutes.",
    rootCause: "Asynchronous policy sync queue backlog delaying role propagation.",
    priorityReasoning:
      "Access inconsistencies can block admin workflows and increase support burden for enterprise tenants.",
    actionPlan: [
      "Drain policy sync backlog and replay failed messages.",
      "Increase consumer concurrency for entitlement events.",
      "Add temporary manual sync endpoint for urgent requests.",
    ],
    diagnosticSteps: [
      "Measure queue depth and consumer lag in policy pipeline.",
      "Audit failed entitlement events by tenant.",
      "Verify cache invalidation triggers in authorization service.",
    ],
  },
  "database issues": {
    mlPriority: "P2",
    recommendedPriority: "P1",
    confidenceScore: 0.81,
    confidenceLabel: "High",
    escalationDecision: "Escalate to DBA on-call if replica lag exceeds 10 minutes.",
    rootCause: "Replica I/O saturation and long-running read transactions.",
    priorityReasoning:
      "Data freshness degradation can invalidate operational decisions and customer reporting commitments.",
    actionPlan: [
      "Throttle non-critical reporting jobs during peak periods.",
      "Re-route heavy analytics to dedicated replica pool.",
      "Terminate long-running read transactions exceeding threshold.",
    ],
    diagnosticSteps: [
      "Check replication lag metrics and write throughput.",
      "Inspect active query list for lock or scan hotspots.",
      "Review storage and IOPS saturation on replica nodes.",
    ],
  },
  "security alerts": {
    mlPriority: "P0",
    recommendedPriority: "P0",
    confidenceScore: 0.95,
    confidenceLabel: "High",
    escalationDecision: "Escalate to security incident commander and initiate containment protocol.",
    rootCause: "Potential credential abuse from anomalous privileged access pattern.",
    priorityReasoning:
      "Possible account compromise requires immediate containment to reduce risk exposure and compliance impact.",
    actionPlan: [
      "Revoke suspicious tokens and enforce privileged credential rotation.",
      "Block malicious IP ranges at edge controls.",
      "Start forensic timeline capture for affected identities.",
    ],
    diagnosticSteps: [
      "Correlate token mint events with geo/IP anomalies.",
      "Validate MFA challenges and success/failure trends.",
      "Review privilege escalation events in audit logs.",
    ],
  },
  "deployment/configuration": {
    mlPriority: "P2",
    recommendedPriority: "P1",
    confidenceScore: 0.75,
    confidenceLabel: "Medium",
    escalationDecision: "Escalate to release manager if production blast radius expands.",
    rootCause: "Incorrect environment scoping in feature flag rollout configuration.",
    priorityReasoning:
      "Misconfiguration can silently alter production behavior and affect multiple customer workflows.",
    actionPlan: [
      "Rollback mis-scoped flag to previous stable state.",
      "Lock write access to production flag set temporarily.",
      "Add pre-deploy validation checks for environment targeting.",
    ],
    diagnosticSteps: [
      "Review last deployment diff and feature flag audit trail.",
      "Compare expected versus actual flag state across tenants.",
      "Validate config propagation timestamps per region.",
    ],
  },
  "email delivery": {
    mlPriority: "P3",
    recommendedPriority: "P2",
    confidenceScore: 0.73,
    confidenceLabel: "Medium",
    escalationDecision: "Escalate to messaging team if queue latency exceeds 15 minutes.",
    rootCause: "Outbound provider throttling and retry queue accumulation.",
    priorityReasoning:
      "Delayed transactional email degrades recovery workflows and can increase support requests.",
    actionPlan: [
      "Shift non-critical campaigns to lower-priority queue.",
      "Increase retry backoff for throttled provider responses.",
      "Fail over critical transactional traffic to backup provider.",
    ],
    diagnosticSteps: [
      "Check provider response codes and throttle limits.",
      "Inspect queue depth and consumer throughput.",
      "Validate webhook delivery confirmation rates.",
    ],
  },
};

function buildSimilarIncidents(ticket: Ticket): AnalysisResult["similar_incidents"] {
  return [
    {
      id: `${ticket.id}-S1`,
      queue: ticket.queue,
      priority: "P1",
      similarity_score: 0.91,
      issue_description: `Historically similar ${ticket.category} event with equivalent service footprint and customer impact pattern.`,
      resolution: "Applied targeted rollback and capacity rebalancing; service restored within 24 minutes.",
    },
    {
      id: `${ticket.id}-S2`,
      queue: ticket.queue,
      priority: "P2",
      similarity_score: 0.84,
      issue_description: `Prior incident involving ${ticket.category} regression triggered by configuration drift.`,
      resolution: "Restored baseline configuration, replayed failed operations, and added post-deploy guardrail checks.",
    },
  ];
}

function buildDebugTrace(ticket: Ticket): AnalysisResult["debug_trace"] {
  return {
    rawRetrieval: [
      `Retrieved 8 historical incidents for category=${ticket.category} queue=${ticket.queue}.`,
      "Top candidate scores before rerank: [0.91, 0.88, 0.84, 0.79, 0.74].",
      "Knowledge base documents included: runbook, postmortem, recent alerts.",
    ],
    rerankedResults: [
      "Rerank model promoted incidents with matching queue ownership and failure signatures.",
      "Cross-tenant but same symptom clusters ranked above local low-signal matches.",
      "Final top-3 relevance: [0.93, 0.89, 0.86].",
    ],
    deduplicatedResults: [
      "Removed 2 near-duplicate incidents from same outage thread.",
      "Collapsed variant alerts sharing identical root cause hash.",
      "Deduplicated context set size: 5.",
    ],
    prompt:
      `Analyze incident ${ticket.id} (${ticket.title}). Determine priority, escalation path, root cause hypothesis, and executable response actions. Return structured operational guidance.`,
    rawLlmOutput:
      `Model classified incident ${ticket.id} as high operational risk based on blast radius indicators, historical similarity, and active customer impact signals.`,
  };
}

export function getMockAnalysisResult(ticket: Ticket): AnalysisResult {
  const defaults = categoryDefaults[ticket.category] ?? categoryDefaults["API errors"];

  return {
    ml_priority: defaults.mlPriority,
    recommended_priority: defaults.recommendedPriority,
    confidence_score: defaults.confidenceScore,
    confidence_label: defaults.confidenceLabel,
    escalation_decision: defaults.escalationDecision,
    root_cause: defaults.rootCause,
    priority_reasoning: defaults.priorityReasoning,
    action_plan: defaults.actionPlan,
    diagnostic_steps: defaults.diagnosticSteps,
    similar_incidents: buildSimilarIncidents(ticket),
    debug_trace: buildDebugTrace(ticket),
  };
}
