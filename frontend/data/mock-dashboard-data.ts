import type { Ticket } from "@/types/ops-decision-engine";

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
