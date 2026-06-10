# 03-design-system.md

## Design direction
Build a premium, enterprise-grade operations dashboard. The visual language should feel calm, sharp, analytical, and trustworthy.

## Keywords
Operational clarity, minimal, premium SaaS, observability, focus, depth, control.

## Avoid
- generic AI gradients
- purple neon styling
- hackathon-style glassmorphism everywhere
- oversized rounded cards
- marketing-site hero aesthetics inside the product
- cluttered KPI overload

## Theme
Use a neutral foundation with one controlled accent color.
Recommended palette:
- background: slate/stone/graphite family
- primary accent: teal or cyan-leaning blue
- success: restrained green
- warning: amber
- error: muted red

## Typography
- Use a clean sans-serif font suitable for dashboards
- Strong hierarchy, compact spacing, readable density
- Headings should feel operational, not editorial

## Layout rules
- Sidebar + topbar desktop layout
- Collapsible or drawer-style nav on mobile
- Card-based but restrained
- Dense data views should still feel breathable
- One primary scroll region per page
- Analytics should be easy to scan in 5 seconds

## Components required
- Sidebar
- Top navbar
- Search bar
- Filter chips
- KPI cards
- Incident table
- Incident status badges
- Severity badges
- SLA risk indicator
- Timeline component
- Alert cluster list
- Recommendation panel
- Upload modal or upload page
- Loading skeletons
- Empty state illustrations/icons
- Toast or inline feedback

## UX behavior
- Dashboard should open with meaningful seeded data
- Filters should visibly affect content
- Incident detail view should support fast scanning
- Every critical state should have hover, active, loading, and empty behavior
- Theme toggle must exist

## Accessibility
- Keyboard navigable
- Strong contrast
- Visible focus states
- Semantic headings and landmarks

## Demo polish
- Populate realistic incident names such as payment-service latency spike, scheduler job failure, auth token refresh error
- Use believable service names and timestamps
- Include at least 20–30 seeded incidents across multiple services
