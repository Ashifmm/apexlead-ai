# Services Architecture Blueprint

This directory hosts the business logic engines for the upcoming stages of the **AI-Powered Web Agency Lead Generation System**.

## Roadmap & Module Structure

| Stage | Service File | Description | Technology |
|---|---|---|---|
| **Stage 2** | `lead_scorer.py` | Calculates opportunity scores (0-100) based on industry value, missing website, or poor design. | Gemini AI / Heuristic rules |
| **Stage 3** | `website_analyzer.py` | Scrapes target URL, checks mobile responsiveness, SSL, page speed, and flags UX flaws. | `httpx`, `BeautifulSoup4`, Gemini Vision |
| **Stage 4** | `outreach_generator.py` | Generates personalized cold emails and Instagram DMs tailored specifically to audit findings. | Google Gemini 2.5 Flash API |
| **Stage 5 & 6** | `demo_generator.py` | Crafts high-converting multi-page website demos with Tailwind CSS (Home, About, Services, Contact) with live hosting. | Google Gemini API + Tailwind CDN + StaticFiles |
| **Stage 8** | `n8n_bridge.py` | Webhook endpoints and event dispatches to trigger external n8n automations. | FastAPI Webhooks |

Each service follows a dependency-injected functional pattern, receiving a database session and lead model, making them easy to unit test and invoke both synchronously or via background tasks.
