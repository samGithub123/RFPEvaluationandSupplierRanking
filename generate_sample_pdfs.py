# -*- coding: utf-8 -*-
"""
generate_sample_pdfs.py - Generate the four artificial supplier RFP PDFs.

What it is for:
    Reproducibly create the four synthetic supplier proposals required by
    the mini-project brief. The documents are fictional and intentionally
    differ in strengths, weaknesses, price, schedule, evidence quality and
    missing information so the evaluation pipeline has meaningful signal.

What it does:
    ✅ Writes four multi-page PDFs into the local `data/` folder:
         Apex_Systems.pdf       - strong tech + security, higher price
         BrightPath_Tech.pdf    - lowest price, weak compliance/experience
         NexaWorks.pdf          - balanced, best implementation + support
         Orbit_Digital.pdf      - strong experience, vague integration plan
    ✅ Each PDF contains: executive summary, solution approach, timeline /
       team / milestones, price table + assumptions, security / compliance /
       risk, and support model / experience / references.

Usage:
    python generate_sample_pdfs.py

Requires: pip install fpdf2
"""

import os

from fpdf import FPDF

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Common RFP context referenced (in slightly different words) by every
# supplier so the documents are comparable against the same requirement.
RFP_CONTEXT = (
    "Northwind Retail Group (the Client) is seeking to replace its legacy "
    "on-premises customer management system with a cloud-based Enterprise "
    "CRM platform. The solution must manage approximately 5 million customer "
    "records, support 2,000 concurrent users, integrate with the Client's "
    "SAP ERP and Mailchimp email platform, and meet SOC 2 Type II and GDPR "
    "requirements. The target implementation window is 12 months with a "
    "budget range of USD 400,000 to USD 900,000."
)


class ProposalPDF(FPDF):
    """Small FPDF subclass that stamps a confidential header on each page."""

    def header(self):
        self.set_font("helvetica", "B", 9)
        self.cell(0, 7, "CONFIDENTIAL - RFP RESPONSE (SYNTHETIC SAMPLE)", align="R", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)


def _heading(pdf, text):
    pdf.set_font("helvetica", "B", 12)
    pdf.multi_cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def _para(pdf, text):
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 5.5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)


def _bullet(pdf, text):
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 5.5, "- " + text, new_x="LMARGIN", new_y="NEXT")


def _table(pdf, headers, rows, col_widths):
    pdf.set_font("helvetica", "", 9)
    with pdf.table(col_widths=tuple(col_widths), text_align="LEFT") as table:
        header_row = table.row()
        for cell in headers:
            header_row.cell(cell)
        for row in rows:
            data_row = table.row()
            for cell in row:
                data_row.cell(cell)
    pdf.ln(3)


def build_pdf(filename, title, subtitle, sections):
    """Render one proposal from a list of section descriptors."""
    pdf = ProposalPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("helvetica", "B", 17)
    pdf.multi_cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "I", 11)
    pdf.multi_cell(0, 6, subtitle, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for section in sections:
        _heading(pdf, section["heading"])
        for para in section.get("paragraphs", []):
            _para(pdf, para)
        for bullet in section.get("bullets", []):
            _bullet(pdf, bullet)
        if "table" in section:
            _table(pdf, section["table"]["headers"], section["table"]["rows"], section["table"]["widths"])
        pdf.ln(2)

    out_path = os.path.join(DATA_DIR, filename)
    pdf.output(out_path)
    return out_path


# --------------------------------------------------------------------------
# Supplier content
# --------------------------------------------------------------------------

APEX = {
    "filename": "Apex_Systems.pdf",
    "title": "Apex Systems - Enterprise CRM Platform Proposal",
    "subtitle": "Enterprise-grade architecture with uncompromising security and scale.",
    "sections": [
        {
            "heading": "1. Executive Summary",
            "paragraphs": [
                RFP_CONTEXT,
                "Apex Systems proposes a cloud-native, microservices-based CRM platform "
                "designed for enterprise scale. Our solution emphasizes architectural "
                "robustness, information security, and long-term scalability. We believe "
                "our platform is the strongest technical fit for the Client's requirement "
                "to support five million records and two thousand concurrent users.",
                "Our proposal carries a premium total price of USD 840,000 and a moderate "
                "twelve-month delivery schedule, reflecting the depth of customization, "
                "security assurance, and enterprise integration work included.",
            ],
        },
        {
            "heading": "2. Proposed Solution and Implementation Approach",
            "paragraphs": [
                "Apex proposes a containerized, Kubernetes-based deployment with a "
                "headless REST/GraphQL API layer, a real-time analytics engine, and "
                "built-in AI-assisted lead scoring. The platform is designed to scale "
                "horizontally and to support the Client's SAP ERP and Mailchimp "
                "integrations through pre-built, governed connectors.",
            ],
            "bullets": [
                "Microservices architecture with independent scaling per workload.",
                "Event-driven data pipeline for real-time customer 360 views.",
                "Pre-built SAP ERP and Mailchimp connectors with reconciliation.",
                "Role-based access control and full audit logging.",
            ],
        },
        {
            "heading": "3. Timeline, Team Structure and Milestones",
            "paragraphs": [
                "Delivery is planned across four phases over twelve months.",
            ],
            "table": {
                "headers": ["Phase", "Milestone", "Month"],
                "rows": [
                    ["Phase 1", "Discovery, security review and integration design", "1-2"],
                    ["Phase 2", "Core CRM build and data model migration", "3-7"],
                    ["Phase 3", "ERP and email integrations, UAT", "8-11"],
                    ["Phase 4", "Production cutover and hypercare", "12"],
                ],
                "widths": [35, 105, 30],
            },
            "bullets": [
                "Dedicated team of 14 including an architect, security lead, and two "
                "integration engineers.",
                "Weekly steering committee and monthly risk review.",
            ],
        },
        {
            "heading": "4. Price Table and Assumptions",
            "table": {
                "headers": ["Item", "Amount (USD)"],
                "rows": [
                    ["Software licenses (annual)", "320,000"],
                    ["Implementation services", "380,000"],
                    ["Integration (SAP + Mailchimp)", "90,000"],
                    ["Training and change management", "50,000"],
                    ["Total", "840,000"],
                ],
                "widths": [130, 40],
            },
            "paragraphs": [
                "Assumptions: pricing is valid for 90 days; excludes migration of legacy "
                "custom objects beyond the standard data model; premium 24/7 support is "
                "available as a separate annual add-on.",
            ],
        },
        {
            "heading": "5. Security, Compliance and Risk Controls",
            "bullets": [
                "SOC 2 Type II and ISO 27001 certified.",
                "GDPR compliance with data residency options in the EU.",
                "AES-256 encryption at rest and TLS 1.2+ in transit.",
                "SSO/SAML, MFA, role-based access, and full audit logs.",
                "Quarterly penetration testing by an independent firm.",
            ],
        },
        {
            "heading": "6. Support Model, Experience and References",
            "paragraphs": [
                "Standard support is provided during business hours; a premium 24/7 "
                "support tier with a 15-minute response SLA is available as an add-on.",
            ],
            "bullets": [
                "Twelve enterprise CRM deployments in retail and distribution.",
                "References available from three enterprise clients upon request.",
                "Average customer tenure of six years.",
            ],
        },
    ],
}

BRIGHTPATH = {
    "filename": "BrightPath_Tech.pdf",
    "title": "BrightPath Tech - Enterprise CRM Platform Proposal",
    "subtitle": "Fast, affordable CRM launch in six months.",
    "sections": [
        {
            "heading": "1. Executive Summary",
            "paragraphs": [
                RFP_CONTEXT,
                "BrightPath Tech proposes the lowest-cost and fastest route to a working "
                "CRM platform: a six-month implementation at a total price of USD 450,000. "
                "We focus on speed and affordability by using a proven out-of-the-box "
                "platform with light configuration rather than heavy custom development.",
                "We want to be transparent that our compliance program is still maturing "
                "and our enterprise track record is more limited than some larger vendors.",
            ],
        },
        {
            "heading": "2. Proposed Solution and Implementation Approach",
            "paragraphs": [
                "BrightPath delivers a configurable SaaS CRM with prebuilt connectors for "
                "common ERP and email platforms. We minimize custom code to accelerate "
                "deployment and keep costs low.",
            ],
            "bullets": [
                "Out-of-the-box CRM with light field and workflow configuration.",
                "Prebuilt connectors for SAP ERP and Mailchimp (limited customization).",
                "Web and mobile access for field teams.",
                "Standard dashboards and reporting.",
            ],
        },
        {
            "heading": "3. Timeline, Team Structure and Milestones",
            "paragraphs": [
                "Delivery is planned across three phases over six months.",
            ],
            "table": {
                "headers": ["Phase", "Milestone", "Month"],
                "rows": [
                    ["Phase 1", "Kickoff and configuration", "1"],
                    ["Phase 2", "Data import and integration setup", "2-4"],
                    ["Phase 3", "UAT and go-live", "5-6"],
                ],
                "widths": [35, 105, 30],
            },
            "bullets": [
                "Team of 8 including a project manager and two configurators.",
                "Fast-tracked schedule relies on minimal customization.",
            ],
        },
        {
            "heading": "4. Price Table and Assumptions",
            "table": {
                "headers": ["Item", "Amount (USD)"],
                "rows": [
                    ["Software licenses (annual)", "180,000"],
                    ["Implementation services", "180,000"],
                    ["Integration setup", "60,000"],
                    ["Training", "30,000"],
                    ["Total", "450,000"],
                ],
                "widths": [130, 40],
            },
            "paragraphs": [
                "Assumptions: pricing is valid for 60 days; excludes migration of legacy "
                "custom objects; custom integration development beyond the prebuilt "
                "connectors is billed separately.",
            ],
        },
        {
            "heading": "5. Security, Compliance and Risk Controls",
            "paragraphs": [
                "BrightPath maintains standard data encryption and access controls. Our "
                "SOC 2 Type I attestation is currently in progress and is expected to be "
                "completed within twelve months.",
            ],
            "bullets": [
                "SOC 2 Type I attestation in progress (Type II not yet available).",
                "Basic GDPR measures; formal data-residency options are limited.",
                "AES-256 encryption at rest and TLS in transit.",
                "No dedicated full-time compliance officer on the delivery team.",
            ],
        },
        {
            "heading": "6. Support Model, Experience and References",
            "paragraphs": [
                "Support is provided by email during business hours. 24/7 support is not "
                "currently available.",
            ],
            "bullets": [
                "Five CRM implementations, primarily for small and mid-sized clients.",
                "Three references available; all are small-business deployments.",
                "Limited enterprise-scale reference history.",
            ],
        },
    ],
}

NEXAWORKS = {
    "filename": "NexaWorks.pdf",
    "title": "NexaWorks - Enterprise CRM Platform Proposal",
    "subtitle": "Balanced delivery with a best-in-class implementation plan and support model.",
    "sections": [
        {
            "heading": "1. Executive Summary",
            "paragraphs": [
                RFP_CONTEXT,
                "NexaWorks proposes a balanced, modular CRM platform with the strongest "
                "implementation plan and support model of this procurement. Our approach "
                "combines a robust technical foundation with a detailed, risk-managed "
                "rollout and a 24/7 support commitment.",
                "Our total price is USD 640,000 with a nine-month delivery schedule.",
            ],
        },
        {
            "heading": "2. Proposed Solution and Implementation Approach",
            "paragraphs": [
                "NexaWorks delivers a modular CRM with phased rollout, strong change "
                "management, and a well-documented integration approach for SAP ERP and "
                "Mailchimp.",
            ],
            "bullets": [
                "Modular architecture allowing incremental feature rollout.",
                "Five-phase implementation with clear exit criteria per phase.",
                "Dedicated change management and user adoption workstream.",
                "Formal risk register reviewed monthly with the Client.",
            ],
        },
        {
            "heading": "3. Timeline, Team Structure and Milestones",
            "paragraphs": [
                "Delivery is planned across five phases over nine months.",
            ],
            "table": {
                "headers": ["Phase", "Milestone", "Month"],
                "rows": [
                    ["Phase 1", "Discovery and requirements baseline", "1"],
                    ["Phase 2", "Foundation build and data migration", "2-4"],
                    ["Phase 3", "Integration and configuration", "5-7"],
                    ["Phase 4", "User acceptance testing", "8"],
                    ["Phase 5", "Cutover, training and hypercare", "9"],
                ],
                "widths": [35, 105, 30],
            },
            "bullets": [
                "Team of 12 including a change manager, data lead, and two integration "
                "specialists.",
                "Risk plan covers data quality, timeline slippage, and adoption.",
            ],
        },
        {
            "heading": "4. Price Table and Assumptions",
            "table": {
                "headers": ["Item", "Amount (USD)"],
                "rows": [
                    ["Software licenses (annual)", "260,000"],
                    ["Implementation services", "290,000"],
                    ["Integration (SAP + Mailchimp)", "60,000"],
                    ["Training and change management", "30,000"],
                    ["Total", "640,000"],
                ],
                "widths": [130, 40],
            },
            "paragraphs": [
                "Assumptions: pricing is valid for 90 days; includes standard data "
                "migration; 24/7 support is included in the license fee.",
            ],
        },
        {
            "heading": "5. Security, Compliance and Risk Controls",
            "bullets": [
                "SOC 2 Type II certified.",
                "GDPR compliant with EU data residency.",
                "AES-256 encryption at rest, TLS 1.2+ in transit.",
                "SSO, MFA, role-based access, and audit logging.",
                "Annual independent penetration testing.",
            ],
        },
        {
            "heading": "6. Support Model, Experience and References",
            "paragraphs": [
                "NexaWorks includes 24/7 support with a 99.9% uptime SLA and a dedicated "
                "customer success manager as standard.",
            ],
            "bullets": [
                "Twenty CRM implementations, including eight enterprise clients.",
                "References available from three enterprise clients.",
                "Strong support model with 24/7 coverage included.",
            ],
        },
    ],
}

ORBIT = {
    "filename": "Orbit_Digital.pdf",
    "title": "Orbit Digital - Enterprise CRM Platform Proposal",
    "subtitle": "Proven experience and flexible delivery for enterprise CRM.",
    "sections": [
        {
            "heading": "1. Executive Summary",
            "paragraphs": [
                RFP_CONTEXT,
                "Orbit Digital brings over fifteen years of enterprise CRM delivery "
                "experience and a strong set of referenceable clients. Our proposal "
                "emphasizes proven methodology and long-term partnership.",
                "Our total price is USD 690,000 with a ten-month delivery schedule. Our "
                "integration approach is intentionally flexible and will be finalized "
                "during discovery.",
            ],
        },
        {
            "heading": "2. Proposed Solution and Implementation Approach",
            "paragraphs": [
                "Orbit proposes a configured enterprise CRM platform built on our "
                "proprietary delivery methodology. We emphasize business-process "
                "alignment and user adoption.",
            ],
            "bullets": [
                "Configured enterprise CRM aligned to the Client's sales and service "
                "processes.",
                "Proprietary delivery methodology with stage gates.",
                "Integration approach to be assessed and finalized during discovery.",
                "Strong training and knowledge-transfer program.",
            ],
        },
        {
            "heading": "3. Timeline, Team Structure and Milestones",
            "paragraphs": [
                "Delivery is planned across four phases over ten months.",
            ],
            "table": {
                "headers": ["Phase", "Milestone", "Month"],
                "rows": [
                    ["Phase 1", "Discovery and integration assessment", "1-2"],
                    ["Phase 2", "Configuration and data migration", "3-6"],
                    ["Phase 3", "Integration build and UAT", "7-9"],
                    ["Phase 4", "Cutover and hypercare", "10"],
                ],
                "widths": [35, 105, 30],
            },
            "bullets": [
                "Team of 11 including a solution architect and training lead.",
                "Integration plan will be finalized after discovery.",
            ],
        },
        {
            "heading": "4. Price Table and Assumptions",
            "table": {
                "headers": ["Item", "Amount (USD)"],
                "rows": [
                    ["Software licenses (annual)", "280,000"],
                    ["Implementation services", "310,000"],
                    ["Integration (scope to be confirmed)", "70,000"],
                    ["Training", "30,000"],
                    ["Total", "690,000"],
                ],
                "widths": [130, 40],
            },
            "paragraphs": [
                "Assumptions: pricing is valid for 90 days; integration estimate assumes "
                "standard SAP ERP and Mailchimp connectors and will be confirmed after "
                "discovery.",
            ],
        },
        {
            "heading": "5. Security, Compliance and Risk Controls",
            "bullets": [
                "SOC 2 Type II certified.",
                "GDPR compliant.",
                "AES-256 encryption at rest and TLS in transit.",
                "SSO, MFA, and role-based access control.",
                "Security risk assessment during discovery.",
            ],
        },
        {
            "heading": "6. Support Model, Experience and References",
            "paragraphs": [
                "Orbit provides 24/7 support with a dedicated account team and a 99.9% "
                "uptime SLA.",
            ],
            "bullets": [
                "Eighteen enterprise CRM implementations over fifteen years.",
                "References available from four large enterprise clients.",
                "Strongest reference base among the responding suppliers.",
            ],
        },
    ],
}

SUPPLIERS = [APEX, BRIGHTPATH, NEXAWORKS, ORBIT]


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    for supplier in SUPPLIERS:
        path = build_pdf(
            supplier["filename"],
            supplier["title"],
            supplier["subtitle"],
            supplier["sections"],
        )
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
