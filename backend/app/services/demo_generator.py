import os
import re
import json
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin
from sqlalchemy.orm import Session

try:
    from app.core.config import settings
    from app.models.lead import Lead
    from app.crud.crud_lead import crud_lead
    from app.schemas.demo import DemoGenerateResponse
    from app.services.gemini_service import gemini_service
except ImportError:
    from backend.app.core.config import settings
    from backend.app.models.lead import Lead
    from backend.app.crud.crud_lead import crud_lead
    from backend.app.schemas.demo import DemoGenerateResponse
    from backend.app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


# Directory where demo website files are written
DEMOS_STORAGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "static", "demos")
)


# Color Theme Configurations for Tailwind CDN
COLOR_THEMES = {
    "indigo": {
        "name": "Modern Indigo",
        "50": "#eef2ff",
        "100": "#e0e7ff",
        "200": "#c7d2fe",
        "500": "#6366f1",
        "600": "#4f46e5",
        "700": "#4338ca",
        "800": "#3730a3",
        "900": "#312e81",
        "accent": "#06b6d4",
    },
    "amber": {
        "name": "Industrial Amber",
        "50": "#fffbeb",
        "100": "#fef3c7",
        "200": "#fde68a",
        "500": "#f59e0b",
        "600": "#d97706",
        "700": "#b45309",
        "800": "#92400e",
        "900": "#78350f",
        "accent": "#ef4444",
    },
    "emerald": {
        "name": "Emerald Growth",
        "50": "#ecfdf5",
        "100": "#d1fae5",
        "200": "#a7f3d0",
        "500": "#10b981",
        "600": "#059669",
        "700": "#047857",
        "800": "#065f46",
        "900": "#064e3b",
        "accent": "#3b82f6",
    },
    "cyan": {
        "name": "Medical & Wellness Cyan",
        "50": "#ecfeff",
        "100": "#cffafe",
        "200": "#a5f3fc",
        "500": "#06b6d4",
        "600": "#0891b2",
        "700": "#0e7490",
        "800": "#155e75",
        "900": "#164e63",
        "accent": "#6366f1",
    },
    "rose": {
        "name": "Electric Rose & Auto",
        "50": "#fff1f2",
        "100": "#ffe4e6",
        "200": "#fecdd3",
        "500": "#f43f5e",
        "600": "#e11d48",
        "700": "#be123c",
        "800": "#9f1239",
        "900": "#881337",
        "accent": "#f59e0b",
    },
    "slate": {
        "name": "Executive Slate",
        "50": "#f8fafc",
        "100": "#f1f5f9",
        "200": "#e2e8f0",
        "500": "#64748b",
        "600": "#475569",
        "700": "#334155",
        "800": "#1e293b",
        "900": "#0f172a",
        "accent": "#38bdf8",
    },
}


class WebsiteDemoGenerator:
    """
    Phase 6 Website Demo Generator:
    Generates multi-page modern HTML prototypes styled with Tailwind CSS.
    Includes:
    - index.html (Homepage with Hero, Trust Proof, Services Preview, Testimonials, CTA)
    - about.html (Company Story, Core Values, Guarantees, Team/Craft)
    - services.html (Full Catalog, Pricing tiers, 4-Step Process, FAQ)
    - contact.html (Interactive Booking/Quote Form with JS Confirmation Modal, Map, Channels)
    """

    def __init__(self):
        os.makedirs(DEMOS_STORAGE_DIR, exist_ok=True)

    def resolve_theme(self, industry: Optional[str], preferred_theme: Optional[str] = None) -> str:
        """Determines best color theme based on industry or user override."""
        if preferred_theme and preferred_theme.lower() in COLOR_THEMES:
            return preferred_theme.lower()

        ind = (industry or "").lower()
        if any(w in ind for w in ["roof", "construct", "plumb", "contractor", "home", "electric", "build"]):
            return "amber"
        elif any(w in ind for w in ["detail", "auto", "car", "motor", "salon", "barber", "beauty"]):
            return "rose"
        elif any(w in ind for w in ["wealth", "finance", "invest", "tax", "law", "legal", "landscap"]):
            return "emerald"
        elif any(w in ind for w in ["dental", "clinic", "health", "medic", "chiro", "doctor", "pool"]):
            return "cyan"
        elif any(w in ind for w in ["food", "restaurant", "cafe", "pizza", "dining", "bakery", "bar"]):
            return "amber"
        elif any(w in ind for w in ["executive", "consult", "real estate", "property", "architect"]):
            return "slate"
        return "indigo"

    def _get_fallback_content(
        self,
        business_name: str,
        industry: str,
        location: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provides rich, bespoke marketing copy for common industries when Gemini is offline."""
        ind = industry.lower()
        loc = location or "your local area"

        if "roof" in ind or "construct" in ind:
            return {
                "tagline": f"Premier Roofing & Exterior Specialists in {loc}",
                "hero_headline": f"Protecting What Matters Most in {loc}",
                "hero_subheadline": f"{business_name} delivers master craftsmanship, Owens Corning certified installations, and 24/7 emergency response for residential and commercial properties.",
                "about_story": f"Founded with a mission to raise the standard of home services in {loc}, {business_name} has grown into one of the region's most trusted exterior contractors. Our licensed and insured specialists take pride in delivering long-lasting protection with honest, upfront pricing.\n\nEvery project is treated as if it were our own home, combining cutting-edge weather-resistant materials with meticulous attention to detail.",
                "core_values": [
                    {"title": "Uncompromising Quality", "desc": "We use only premium architectural shingles and structural materials backed by lifetime warranties."},
                    {"title": "Upfront Transparent Pricing", "desc": "Detailed line-item quotes with zero surprise fees or hidden change orders."},
                    {"title": "Rapid Storm Response", "desc": "Priority emergency tarping and damage assessments when severe weather strikes."},
                    {"title": "100% Satisfaction Guarantee", "desc": "Final walkthrough inspection before we consider any project complete."}
                ],
                "services": [
                    {
                        "title": "Complete Roof Replacement",
                        "description": "Full tear-off and architectural shingle installation with enhanced ventilation and leak barrier protection.",
                        "price_hint": "Free Inspection & Quote",
                        "features": ["Lifetime Architectural Shingles", "Class-4 Impact Resistance", "Transferable Manufacturer Warranty"]
                    },
                    {
                        "title": "Emergency Leak Repair",
                        "description": "Fast-response troubleshooting and targeted repairs for missing shingles, flashing leaks, and wind damage.",
                        "price_hint": "Starting at $299",
                        "features": ["Same-Day Service Available", "Infrared Moisture Detection", "Complete Weatherproofing Seal"]
                    },
                    {
                        "title": "Gutter & Downspout Systems",
                        "description": "Seamless aluminum gutters custom-extruded on-site to channel rainwater away from your foundation.",
                        "price_hint": "From $950 installed",
                        "features": ["Seamless 6-inch Heavy Gauge", "Leaf Protection Guard Options", "Color-Matched to Your Siding"]
                    },
                    {
                        "title": "Storm & Hail Damage Audit",
                        "description": "Comprehensive drone and physical inspection report with photographic evidence for insurance claims.",
                        "price_hint": "100% Complimentary",
                        "features": ["High-Res Drone Imagery", "Insurance Claim Assistance", "Detailed Repair Roadmap"]
                    }
                ],
                "testimonials": [
                    {
                        "name": "Marcus Henderson",
                        "role": f"Homeowner in {loc}",
                        "quote": f"{business_name} replaced our storm-damaged roof in two days flat. Cleaned up every nail and worked seamlessly with our adjuster. Couldn't recommend them more!",
                        "stars": 5
                    },
                    {
                        "name": "Sarah Jenkins",
                        "role": f"Property Manager, {loc}",
                        "quote": "Honest, punctual, and top-tier workmanship. Their instant quote was spot-on with no surprise charges.",
                        "stars": 5
                    },
                    {
                        "name": "David Ramirez",
                        "role": f"Local Resident, {loc}",
                        "quote": f"The best roofing team in {loc}. Their crew was courteous, fast, and the new architectural shingles look incredible.",
                        "stars": 5
                    }
                ],
                "faqs": [
                    {"question": "How quickly can you inspect my roof?", "answer": "We typically offer same-day or next-day on-site inspections throughout the greater area."},
                    {"question": "Are you licensed and insured?", "answer": f"Yes, {business_name} maintains full general liability, worker's compensation, and state licensing."},
                    {"question": "How long does a full roof replacement take?", "answer": "Most standard residential roofs are completed in just 1 to 2 days, including comprehensive cleanup."},
                    {"question": "Do you assist with insurance claims?", "answer": "Yes, our team provides complete photographic documentation and meets directly with your adjuster."}
                ],
                "cta_headline": f"Get Your Free Roof Inspection with {business_name}",
                "cta_subheadline": "Contact our certified specialists today for an upfront, no-obligation estimate."
            }

        elif "detail" in ind or "auto" in ind:
            return {
                "tagline": f"Master Auto Detailing & Ceramic Studio in {loc}",
                "hero_headline": f"Precision Paint Correction & Ceramic Coatings in {loc}",
                "hero_subheadline": f"{business_name} elevates fine automobiles with multi-stage paint correction, self-healing ceramic protection, and bespoke interior restoration.",
                "about_story": f"{business_name} was born out of an obsessive passion for automotive perfection. Serving the finest vehicles in {loc}, our climate-controlled studio utilizes state-of-the-art dual-action polishers, infrared curing lamps, and professional-grade ceramic formulas.\n\nWe treat every vehicle as a rolling work of art, guaranteeing showroom-depth gloss and long-term surface protection.",
                "core_values": [
                    {"title": "Obsessive Craftsmanship", "desc": "Multi-stage test spots to achieve 90%+ defect removal without compromising clear coat."},
                    {"title": "Exclusive Studio Environment", "desc": "Fully dust-controlled, LED-illuminated studio built specifically for precision finishing."},
                    {"title": "Certified Protection", "desc": "Authorized installer of 3, 5, and 9-year warrantied ceramic coatings."},
                    {"title": "Personalized Client Care", "desc": "Detailed before-and-after paint depth analysis and dedicated maintenance guidance."}
                ],
                "services": [
                    {
                        "title": "Signature Paint Correction",
                        "description": "Multi-stage compound and jewel polish eliminating swirl marks, holograms, scratches, and oxidation.",
                        "price_hint": "Starting at $499",
                        "features": ["Paint Depth Gauge Verification", "Up to 95% Defect Removal", "Mirror-Finish High Gloss Polish"]
                    },
                    {
                        "title": "9H Ceramic Coating Protection",
                        "description": "Ultra-hydrophobic chemical bond shielding clear coat from UV rays, acid rain, bird droppings, and light marring.",
                        "price_hint": "From $899 (3-Year)",
                        "features": ["Extreme Hydrophobic Beading", "Carfax Recorded Warranty", "Glass & Wheel Face Coating Included"]
                    },
                    {
                        "title": "Bespoke Interior Rejuvenation",
                        "description": "Steam sanitization, pH-balanced leather conditioning, extraction shampooing, and UV interior barrier coating.",
                        "price_hint": "Starting at $249",
                        "features": ["Hot Water Extraction", "Matte OEM Leather Conditioning", "Odor Neutralization Treatment"]
                    },
                    {
                        "title": "Track & Exotic Maintenance Detail",
                        "description": "Gentle two-bucket deionized wash, iron decontamination, and synthetic sealant application.",
                        "price_hint": "Starting at $175",
                        "features": ["100% Touchless Air Blow Dry", "Wheels-Off Deep Clean Option", "Safe for Matte & PPF Finishes"]
                    }
                ],
                "testimonials": [
                    {
                        "name": "Alex Vance",
                        "role": f"Porsche 911 GT3 Owner, {loc}",
                        "quote": f"The level of detail at {business_name} is unmatched. The ceramic coating made the paint look deeper than the day I picked it up from the dealer.",
                        "stars": 5
                    },
                    {
                        "name": "Elena Rostova",
                        "role": f"BMW M4 Competition, {loc}",
                        "quote": "Brought in my black M4 with heavy swirl marks. Returned to a flawless mirror finish. True artisans.",
                        "stars": 5
                    },
                    {
                        "name": "Chris Taylor",
                        "role": f"Local Enthusiast, {loc}",
                        "quote": f"Hands down the premier auto studio in {loc}. Clear communication, immaculate facility, and incredible results.",
                        "stars": 5
                    }
                ],
                "faqs": [
                    {"question": "How long does a ceramic coating application take?", "answer": "Paint correction and ceramic coating typically require 24 to 48 hours for proper prep and infrared curing."},
                    {"question": "Can ceramic coating prevent rock chips?", "answer": "Ceramic coatings provide chemical and scratch resistance; for direct rock chip protection, we recommend PPF."},
                    {"question": "How should I wash my car after ceramic coating?", "answer": "We provide a complimentary aftercare guide with recommended pH-neutral soaps and microfiber wash mitts."},
                    {"question": "Do you require an in-person estimate?", "answer": "You can book directly or visit our studio for a quick 10-minute paint inspection and custom quote."}
                ],
                "cta_headline": f"Reserve Your Studio Slot at {business_name}",
                "cta_subheadline": "Limited weekly appointments to ensure maximum focus on every vehicle."
            }

        elif "food" in ind or "restaurant" in ind or "cafe" in ind or "bakery" in ind:
            return {
                "tagline": f"Authentic Culinary Experience & Dining in {loc}",
                "hero_headline": f"Taste the Tradition & Art of Authentic Dining in {loc}",
                "hero_subheadline": f"{business_name} invites you to savor artisanal recipes, locally sourced ingredients, and warm hospitality in the heart of {loc}.",
                "about_story": f"At {business_name}, we believe food is more than nourishment — it is a celebration of community, heritage, and genuine flavor. Located in {loc}, our kitchen pairs time-honored culinary traditions with fresh seasonal produce from regional farms.\n\nFrom casual weeknight dinners to private family celebrations, we create memorable moments around the table.",
                "core_values": [
                    {"title": "Farm-to-Table Freshness", "desc": "Locally sourced produce, artisanal cheeses, and prime cuts delivered daily."},
                    {"title": "Scratch-Made Daily", "desc": "Handcrafted pasta, baked breads, and slow-simmered sauces prepared from scratch every morning."},
                    {"title": "Warm Hospitality", "desc": "An inviting atmosphere where every guest is welcomed as part of our extended family."},
                    {"title": "Curated Wine & Cocktails", "desc": "Thoughtfully selected vintages and signature cocktails designed to complement our menu."}
                ],
                "services": [
                    {
                        "title": "Signature Dinner Menu",
                        "description": "A curated seasonal collection of artisanal mains, house-made pastas, and wood-fired specialties.",
                        "price_hint": "Entrees $18 - $42",
                        "features": ["Handcrafted Daily Pastas", "Prime Dry-Aged Cuts", "Vegetarian & Gluten-Free Options"]
                    },
                    {
                        "title": "Private Dining & Events",
                        "description": "Exclusive dining room reservations for corporate gatherings, rehearsal dinners, and intimate celebrations.",
                        "price_hint": "Custom Group Menus",
                        "features": ["Dedicated Sommelier Service", "Custom Printed Menus", "Audiovisual Setup Available"]
                    },
                    {
                        "title": "Artisanal Catering Services",
                        "description": "Full-service off-site catering bringing our celebrated culinary experience to your venue or office.",
                        "price_hint": "From $35 / guest",
                        "features": ["Hot Chafing Dish Setup", "Professional Service Staff", "Custom Dietary Adaptations"]
                    },
                    {
                        "title": "Chef's Weekend Tasting",
                        "description": "A five-course culinary journey showcasing rare ingredients and experimental seasonal dishes.",
                        "price_hint": "$85 / person",
                        "features": ["Optional Wine Pairing", "Chef Table Introduction", "Available Friday - Sunday"]
                    }
                ],
                "testimonials": [
                    {
                        "name": "Sophia Moretti",
                        "role": f"Food Critic, {loc} Daily",
                        "quote": f"An extraordinary gem in {loc}. The homemade truffle gnocchi and hospitality make {business_name} an unforgettable experience.",
                        "stars": 5
                    },
                    {
                        "name": "Jonathan Burke",
                        "role": "Verified Diner",
                        "quote": "Hosted my wife's 40th birthday here in the private room. The service, pacing, and food were simply flawless.",
                        "stars": 5
                    },
                    {
                        "name": "Claire Dupont",
                        "role": f"Local Resident, {loc}",
                        "quote": "Our favorite weekend spot. The ambiance is warm and the scratch-made specials never disappoint.",
                        "stars": 5
                    }
                ],
                "faqs": [
                    {"question": "Do I need a reservation?", "answer": "Reservations are strongly recommended for Friday and Saturday evenings, but walk-ins are always welcomed at our bar and patio."},
                    {"question": "Do you accommodate dietary restrictions?", "answer": "Yes, our culinary team readily accommodates vegetarian, vegan, gluten-free, and nut-allergy requirements."},
                    {"question": "Is private event booking available?", "answer": "Yes, our private dining room accommodates groups from 12 to 50 guests. Please contact us in advance."},
                    {"question": "Do you offer takeout or delivery?", "answer": "Yes, direct online ordering is available with curbside pickup during operating hours."}
                ],
                "cta_headline": f"Reserve Your Table at {business_name}",
                "cta_subheadline": "Experience authentic culinary excellence in {loc}. Book your reservation online in seconds."
            }

        # General / Professional Services Fallback
        return {
            "tagline": f"Leading {industry} Solutions in {loc}",
            "hero_headline": f"Exceptional {industry} Built for Results in {loc}",
            "hero_subheadline": f"{business_name} provides premier solutions, trusted expertise, and dedicated customer service tailored to clients across {loc}.",
            "about_story": f"At {business_name}, we are committed to delivering unmatched standards of excellence for every client in {loc}. With years of industry experience and a reputation for reliability, our team combines modern methodologies with personalized attention.\n\nWhether you need ongoing support or a dedicated consultation, we take the time to understand your goals and deliver measurable outcomes.",
            "core_values": [
                {"title": "Client-First Focus", "desc": "Every engagement is customized to your unique objectives and priorities."},
                {"title": "Transparent Communication", "desc": "Clear milestones, direct contact with decision makers, and no confusing jargon."},
                {"title": "Proven Track Record", "desc": "Backed by dozens of successful local case studies and five-star reviews."},
                {"title": "Modern Innovation", "desc": "Utilizing the latest technology and best practices to ensure peak efficiency."}
            ],
            "services": [
                {
                    "title": f"Comprehensive {industry} Consultation",
                    "description": "Full diagnostic assessment identifying your highest leverage opportunities and immediate action plan.",
                    "price_hint": "Complimentary",
                    "features": ["Personalized Needs Assessment", "Actionable Roadmap", "Zero Pressure Discussion"]
                },
                {
                    "title": f"Standard {industry} Package",
                    "description": "Complete turnkey execution designed for fast turnaround, maximum reliability, and high satisfaction.",
                    "price_hint": "Starting at $450",
                    "features": ["Full Project Scope", "Dedicated Point of Contact", "100% Quality Assurance"]
                },
                {
                    "title": f"Premium Enterprise Solutions",
                    "description": "Advanced strategy, priority scheduling, and customized execution for complex or high-volume requirements.",
                    "price_hint": "Custom Quote",
                    "features": ["Priority 24/7 Support", "Custom Deliverables", "Ongoing Maintenance Options"]
                },
                {
                    "title": f"Ongoing Maintenance & Care",
                    "description": "Proactive service agreements ensuring consistent performance, peace of mind, and predictable budgeting.",
                    "price_hint": "Flexible Monthly Plans",
                    "features": ["Scheduled Checkups", "Emergency Priority Queue", "Discounts on Add-Ons"]
                }
            ],
            "testimonials": [
                {
                    "name": "Robert Sterling",
                    "role": f"Business Executive, {loc}",
                    "quote": f"Working with {business_name} was the best decision we made. Professional, prompt, and exceeded all expectations.",
                    "stars": 5
                },
                {
                    "name": "Maria Santos",
                    "role": f"Client in {loc}",
                    "quote": "Incredible communication and genuine care for their craft. Highly recommend them to anyone looking for quality.",
                    "stars": 5
                },
                {
                    "name": "Keith Holloway",
                    "role": "Verified Customer",
                    "quote": "Fast response, honest estimates, and immaculate delivery. A true 5-star service experience.",
                    "stars": 5
                }
            ],
            "faqs": [
                {"question": "How do I schedule an appointment?", "answer": "You can submit an inquiry via our contact form or call our direct phone line during regular hours."},
                {"question": "What is your typical turnaround time?", "answer": "Most consultations and standard projects begin within 24 to 48 hours of initial contact."},
                {"question": "Do you provide written estimates?", "answer": "Yes, all proposals are detailed in writing with complete scope breakdown prior to commencement."},
                {"question": "Are consultations free?", "answer": "Yes, our initial discovery consultation is 100% complimentary with no obligation."}
            ],
            "cta_headline": f"Ready to Partner with {business_name}?",
            "cta_subheadline": f"Contact our expert team today to schedule your consultation in {loc}."
        }

    def _generate_gemini_content(
        self,
        business_name: str,
        industry: str,
        location: str,
        notes: str,
        custom_instructions: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Invokes Gemini to generate customized marketing copy."""
        if not gemini_service.is_configured:
            return None

        prompt = (
            f"Generate high-converting, professional website content for a multi-page business website:\n"
            f"- Business Name: {business_name}\n"
            f"- Industry / Niche: {industry}\n"
            f"- Location: {location}\n"
            f"- Business Context: {notes or 'None'}\n"
            f"- Agency Custom Instructions: {custom_instructions or 'None'}\n\n"
            f"Requirements:\n"
            f"1. Tagline: short, punchy marketing phrase.\n"
            f"2. Hero Headline & Subheadline: high-converting value proposition for local searchers.\n"
            f"3. About Story: 2 realistic, engaging paragraphs about the business founding, craftsmanship, and dedication to {location}.\n"
            f"4. Core Values: array of 4 objects with 'title' and 'desc'.\n"
            f"5. Services: array of 4 distinct services with 'title', 'description', 'price_hint', and 'features' (list of 3 checkmark bullets).\n"
            f"6. Testimonials: array of 3 realistic local client reviews with 'name', 'role' (e.g. 'Homeowner in {location}'), 'quote', and 'stars' (5).\n"
            f"7. FAQs: array of 4 common customer questions with clear, reassuring 'answer'.\n"
            f"8. CTA Headline & Subheadline: compelling call to action.\n\n"
            f"Return ONLY valid JSON matching this schema."
        )

        try:
            client = gemini_service._get_client()
            target_model = gemini_service.default_model

            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3
                }
            )

            if response.text:
                data = json.loads(response.text)
                if "hero_headline" in data and "services" in data:
                    return data
        except Exception as e:
            logger.warning(f"Gemini demo copy generation failed, using intelligent fallback: {e}")

        return None

    def _render_nav(
        self,
        business_name: str,
        phone: Optional[str],
        active_page: str,
        theme_id: str
    ) -> str:
        """Renders sticky floating responsive navbar with glassmorphism, glowing CTA, and mobile menu."""
        pages = [
            ("index.html", "Home"),
            ("about.html", "About Us"),
            ("services.html", "Services"),
            ("contact.html", "Contact & Booking"),
        ]

        nav_links_html = ""
        mobile_links_html = ""

        for file_name, label in pages:
            is_active = (active_page == file_name)
            if is_active:
                nav_links_html += (
                    f'<a href="{file_name}" class="text-primary-600 font-bold border-b-2 border-primary-600 pb-1">{label}</a>\n'
                )
                mobile_links_html += (
                    f'<a href="{file_name}" class="block py-2 text-primary-600 font-bold border-l-4 border-primary-600 pl-3 bg-primary-50/50">{label}</a>\n'
                )
            else:
                nav_links_html += (
                    f'<a href="{file_name}" class="text-slate-600 hover:text-primary-600 font-medium transition-colors">{label}</a>\n'
                )
                mobile_links_html += (
                    f'<a href="{file_name}" class="block py-2 text-slate-700 hover:text-primary-600 font-medium pl-3">{label}</a>\n'
                )

        phone_clean = phone or "(555) 234-5678"

        return f'''
        <!-- Top Announcement Bar -->
        <div class="bg-slate-900 text-slate-300 text-xs py-2 px-4 border-b border-slate-800">
            <div class="max-w-7xl mx-auto flex flex-wrap justify-between items-center gap-2">
                <div class="flex items-center gap-3">
                    <span class="inline-flex items-center gap-1 font-medium text-primary-400">
                        <i data-lucide="sparkles" class="w-3.5 h-3.5 text-primary-400"></i>
                        Accepting New Clients This Month
                    </span>
                    <span class="hidden sm:inline text-slate-600">|</span>
                    <span class="hidden sm:inline text-slate-400">100% Satisfaction Guarantee</span>
                </div>
                <div class="flex items-center gap-4">
                    <a href="tel:{phone_clean}" class="hover:text-white flex items-center gap-1.5 transition-colors">
                        <i data-lucide="phone" class="w-3.5 h-3.5 text-primary-400"></i>
                        <span>{phone_clean}</span>
                    </a>
                </div>
            </div>
        </div>

        <!-- Sticky Floating Glassmorphism Header & Nav -->
        <header class="sticky top-4 z-40 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 transition-all duration-300">
            <div class="rounded-2xl bg-white/85 backdrop-blur-xl border border-white/50 shadow-lg shadow-slate-900/5 px-6 h-20 flex items-center justify-between">
                <!-- Brand Logo -->
                <a href="index.html" class="flex items-center gap-2.5 group">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-600 text-white flex items-center justify-center font-black shadow-md shadow-primary-500/20 group-hover:scale-105 transition-transform">
                        <i data-lucide="check" class="w-5 h-5"></i>
                    </div>
                    <div>
                        <span class="text-lg font-bold text-slate-900 tracking-tight block leading-tight">{business_name}</span>
                        <span class="text-[10px] font-semibold tracking-wider uppercase text-primary-600 flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                            Verified Local Business
                        </span>
                    </div>
                </a>

                <!-- Desktop Navigation -->
                <nav class="hidden md:flex items-center gap-8 text-sm">
                    {nav_links_html}
                </nav>

                <!-- Glowing CTA Action Button -->
                <div class="hidden sm:flex items-center gap-3">
                    <a href="contact.html" class="relative group overflow-hidden inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 text-white font-semibold text-sm shadow-[0_0_20px_rgba(99,102,241,0.35)] hover:shadow-[0_0_30px_rgba(99,102,241,0.55)] active:scale-95 transition-all">
                        <span class="relative z-10 flex items-center gap-1.5">
                            <span>Get A Quote</span>
                            <i data-lucide="arrow-right" class="w-4 h-4"></i>
                        </span>
                        <div class="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                    </a>
                </div>

                <!-- Mobile Hamburger Button -->
                <button id="mobile-nav-toggle" class="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100" aria-label="Toggle Navigation">
                    <i data-lucide="menu" class="w-6 h-6"></i>
                </button>
            </div>

            <!-- Mobile Menu Dropdown -->
            <div id="mobile-menu" class="hidden md:hidden mt-2 rounded-2xl border border-slate-200 bg-white shadow-xl px-4 pt-2 pb-4 space-y-1">
                {mobile_links_html}
                <div class="pt-3 border-t border-slate-100">
                    <a href="contact.html" class="block w-full text-center py-2.5 rounded-xl bg-primary-600 text-white font-semibold text-sm">
                        Schedule Online Consultation
                    </a>
                </div>
            </div>
        </header>
        '''

    def _render_footer(
        self,
        business_name: str,
        location: str,
        phone: Optional[str],
        email: Optional[str],
        industry: str
    ) -> str:
        """Renders comprehensive footer with contact channels and agency demo signature."""
        phone_val = phone or "(555) 234-5678"
        email_val = email or f"contact@{re.sub(r'[^a-zA-Z0-9]', '', business_name.lower())}.com"
        digits = re.sub(r'[^0-9]', '', phone_val)
        if len(digits) == 10:
            wa_phone = f"91{digits}"
        elif len(digits) > 10:
            wa_phone = digits
        else:
            wa_phone = "919811001122"
        encoded_biz = business_name.replace(" ", "%20")

        return f'''
        <footer class="bg-slate-950 text-slate-400 text-sm border-t border-slate-900 pt-16 pb-12 mt-16">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 pb-12 border-b border-slate-800/80">
                    <!-- Col 1: About -->
                    <div class="space-y-4">
                        <div class="flex items-center gap-2 text-white font-bold text-lg">
                            <div class="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center text-white font-black text-xs">
                                ✓
                            </div>
                            <span>{business_name}</span>
                        </div>
                        <p class="text-xs text-slate-400 leading-relaxed">
                            Dedicated to delivering top-tier {industry} across {location} and surrounding communities. Quality craftsmanship guaranteed on every project.
                        </p>
                        <div class="flex items-center gap-3 pt-2">
                            <span class="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-semibold bg-emerald-950/60 border border-emerald-800/50 px-2.5 py-1 rounded-full">
                                ● Licensed & Insured
                            </span>
                        </div>
                    </div>

                    <!-- Col 2: Navigation Links -->
                    <div class="space-y-3">
                        <h4 class="text-white font-semibold text-xs uppercase tracking-wider">Quick Navigation</h4>
                        <ul class="space-y-2 text-xs">
                            <li><a href="index.html" class="hover:text-primary-400 transition-colors">Home Page</a></li>
                            <li><a href="about.html" class="hover:text-primary-400 transition-colors">About Our Company</a></li>
                            <li><a href="services.html" class="hover:text-primary-400 transition-colors">Services & Pricing</a></li>
                            <li><a href="contact.html" class="hover:text-primary-400 transition-colors">Book An Appointment</a></li>
                        </ul>
                    </div>

                    <!-- Col 3: Direct Contact -->
                    <div class="space-y-3">
                        <h4 class="text-white font-semibold text-xs uppercase tracking-wider">Contact Details</h4>
                        <ul class="space-y-2.5 text-xs">
                            <li class="flex items-center gap-2">
                                <span class="text-primary-400">📞</span>
                                <a href="tel:{phone_val}" class="hover:text-white">{phone_val}</a>
                            </li>
                            <li class="flex items-center gap-2">
                                <span class="text-primary-400">✉️</span>
                                <a href="mailto:{email_val}" class="hover:text-white">{email_val}</a>
                            </li>
                            <li class="flex items-center gap-2">
                                <span class="text-primary-400">📍</span>
                                <span>{location}</span>
                            </li>
                        </ul>
                    </div>

                    <!-- Col 4: Business Hours -->
                    <div class="space-y-3">
                        <h4 class="text-white font-semibold text-xs uppercase tracking-wider">Business Hours</h4>
                        <div class="space-y-1.5 text-xs text-slate-400">
                            <div class="flex justify-between"><span>Mon - Fri:</span> <span class="text-slate-200">8:00 AM - 6:00 PM</span></div>
                            <div class="flex justify-between"><span>Saturday:</span> <span class="text-slate-200">9:00 AM - 2:00 PM</span></div>
                            <div class="flex justify-between"><span>Sunday:</span> <span class="text-slate-500">Emergency Call Only</span></div>
                        </div>
                    </div>
                </div>

                <!-- Bottom Copyright & Agency Ribbon -->
                <div class="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
                    <p>© 2026 {business_name}. All rights reserved.</p>
                    <div class="flex items-center gap-2 text-slate-400">
                        <span class="inline-flex items-center gap-1 font-semibold text-primary-400 bg-slate-900 border border-slate-800 px-3 py-1 rounded-lg">
                            ⚡ Prototype Demo engineered by ApexLead AI
                        </span>
                    </div>
                </div>
            </div>
        </footer>

        <!-- Floating WhatsApp CTA Button -->
        <a href="https://wa.me/{wa_phone}?text=Hi%20{encoded_biz}%2C%20I%20would%20like%20to%20inquire%20about%20your%20services." target="_blank" rel="noopener noreferrer" class="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 bg-[#25D366] hover:bg-[#20ba59] text-white px-4 py-3 rounded-full shadow-2xl hover:scale-105 active:scale-95 transition-all duration-300 group" title="Chat on WhatsApp">
            <svg class="w-6 h-6 fill-current" viewBox="0 0 24 24">
                <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.592 2.654-.696c1.001.597 1.77.853 2.806.853 3.18 0 5.767-2.587 5.767-5.766.001-3.18-2.585-5.736-5.767-5.736zm3.365 8.163c-.149.421-.861.777-1.196.828-.335.051-.772.079-2.222-.52-1.854-.766-3.036-2.654-3.129-2.778-.093-.124-.755-.999-.755-1.905 0-.906.477-1.353.647-1.539.17-.186.372-.232.496-.232.124 0 .248.002.356.007.113.006.264-.043.413.315.154.372.525 1.282.571 1.375.046.093.077.202.016.326-.062.124-.093.202-.186.31-.093.109-.196.243-.28.326-.093.093-.19.194-.082.38.109.186.483.797 1.036 1.29 1.139.92 1.492.932 1.709 1.042.217.109.345.093.473-.054.128-.147.548-.638.695-.855.147-.217.294-.182.496-.109.202.074 1.282.605 1.503.714.221.109.368.163.422.256.054.093.054.542-.095.963z"/>
            </svg>
            <span class="font-bold text-xs tracking-wide hidden sm:inline-block">Chat on WhatsApp</span>
        </a>

        <!-- Interactive Floating Navigation Bar for Demo Preview -->
        <div class="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-full px-4 py-2 shadow-2xl flex items-center gap-3 text-xs text-white">
            <span class="font-bold text-primary-400 flex items-center gap-1">
                <span>⚡</span> Demo Pages:
            </span>
            <div class="flex items-center gap-1">
                <a href="index.html" class="px-2.5 py-1 rounded-full hover:bg-slate-800 transition-colors">Home</a>
                <a href="about.html" class="px-2.5 py-1 rounded-full hover:bg-slate-800 transition-colors">About</a>
                <a href="services.html" class="px-2.5 py-1 rounded-full hover:bg-slate-800 transition-colors">Services</a>
                <a href="contact.html" class="px-2.5 py-1 rounded-full hover:bg-slate-800 transition-colors">Contact</a>
            </div>
        </div>

        <!-- AOS Animate On Scroll Library JS & Lucide Init -->
        <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                if (typeof AOS !== 'undefined') {{
                    AOS.init({{ duration: 800, once: true }});
                }}
                if (typeof lucide !== 'undefined') {{
                    lucide.createIcons();
                }}
            }});
        </script>

        <script>
            // Mobile Menu Toggle
            const toggleBtn = document.getElementById('mobile-nav-toggle');
            const menu = document.getElementById('mobile-menu');
            if (toggleBtn && menu) {{
                toggleBtn.addEventListener('click', () => {{
                    menu.classList.toggle('hidden');
                }});
            }}
        </script>
        '''

    def _render_head(self, title: str, business_name: str, theme: Dict[str, str]) -> str:
        """Constructs HTML <head> with Google Fonts, AOS CDN, Lucide Icons, and Tailwind CDN."""
        return f'''<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {business_name}</title>
    <!-- Google Fonts: Plus Jakarta Sans -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- AOS (Animate On Scroll) CSS -->
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
    <!-- Lucide Icons CDN -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>

    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
                    }},
                    colors: {{
                        primary: {{
                            50: '{theme["50"]}',
                            100: '{theme["100"]}',
                            200: '{theme["200"]}',
                            500: '{theme["500"]}',
                            600: '{theme["600"]}',
                            700: '{theme["700"]}',
                            800: '{theme["800"]}',
                            900: '{theme["900"]}',
                        }},
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col">
'''

    def generate_index_page(
        self,
        business_name: str,
        industry: str,
        location: str,
        phone: Optional[str],
        email: Optional[str],
        content: Dict[str, Any],
        theme: Dict[str, str],
        theme_id: str
    ) -> str:
        """Generates rich, high-converting index.html Homepage."""
        head = self._render_head(f"Home", business_name, theme)
        nav = self._render_nav(business_name, phone, "index.html", theme_id)
        footer = self._render_footer(business_name, location, phone, email, industry)

        services_cards_html = ""
        for idx, svc in enumerate(content.get("services", [])[:3]):
            features_html = "".join(
                f'<li class="flex items-center gap-2 text-xs text-slate-600"><span class="text-primary-600 font-bold">✓</span> {feat}</li>'
                for feat in svc.get("features", [])
            )
            svc_delay = (idx + 1) * 150
            services_cards_html += f'''
            <div data-aos="fade-up" data-aos-delay="{svc_delay}" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-lg transition-all flex flex-col justify-between group">
                <div class="space-y-3">
                    <div class="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center font-bold text-xl group-hover:scale-105 transition-transform">
                        ★
                    </div>
                    <div class="flex items-center justify-between gap-2">
                        <h3 class="text-lg font-bold text-slate-900 group-hover:text-primary-600 transition-colors">{svc["title"]}</h3>
                        <span class="rounded-full bg-slate-100 text-slate-700 px-2.5 py-0.5 text-xs font-semibold">{svc.get("price_hint", "")}</span>
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">{svc["description"]}</p>
                    <ul class="space-y-1.5 pt-2 border-t border-slate-100">
                        {features_html}
                    </ul>
                </div>
                <div class="pt-5">
                    <a href="services.html" class="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-600 hover:text-primary-700">
                        <span>Learn More</span>
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                    </a>
                </div>
            </div>
            '''

        testimonials_html = ""
        for idx, t in enumerate(content.get("testimonials", [])):
            stars_html = "★" * t.get("stars", 5)
            t_delay = (idx + 1) * 150
            testimonials_html += f'''
            <div data-aos="fade-up" data-aos-delay="{t_delay}" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between">
                <div class="space-y-3">
                    <div class="text-amber-400 text-sm tracking-widest">{stars_html}</div>
                    <p class="text-xs text-slate-700 italic leading-relaxed">"{t['quote']}"</p>
                </div>
                <div class="pt-4 border-t border-slate-100 mt-4 flex items-center gap-3">
                    <div class="w-9 h-9 rounded-full bg-primary-100 text-primary-700 font-bold flex items-center justify-center text-xs">
                        {t['name'][0]}
                    </div>
                    <div>
                        <h4 class="text-xs font-bold text-slate-900">{t['name']}</h4>
                        <span class="text-[10px] text-slate-500">{t.get('role', 'Verified Client')}</span>
                    </div>
                </div>
            </div>
            '''

        body = f'''
        {head}
        {nav}

        <main class="flex-1 space-y-12 sm:space-y-20">
            <!-- Hero Section -->
            <section class="relative overflow-hidden bg-gradient-to-b from-primary-50/70 via-white to-slate-50 pt-16 pb-20 lg:pt-24 lg:pb-28">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
                        <div class="lg:col-span-7 space-y-6 text-center lg:text-left" data-aos="fade-up">
                            <div class="inline-flex items-center gap-2 rounded-full border border-primary-200 bg-primary-100/60 px-4 py-1.5 text-xs font-bold text-primary-800 shadow-sm">
                                <i data-lucide="award" class="w-3.5 h-3.5 text-primary-600"></i>
                                <span>⭐ Top-Rated {industry}</span>
                                <span>•</span>
                                <span>{location}</span>
                            </div>
                            <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.15]">
                                {content.get("hero_headline")}
                            </h1>
                            <p class="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto lg:mx-0 leading-relaxed font-normal">
                                {content.get("hero_subheadline")}
                            </p>
                            <div class="flex flex-wrap items-center justify-center lg:justify-start gap-4 pt-2">
                                <a href="contact.html" class="relative group overflow-hidden inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 text-white font-bold text-sm shadow-[0_0_25px_rgba(99,102,241,0.4)] hover:shadow-[0_0_35px_rgba(99,102,241,0.6)] active:scale-95 transition-all">
                                    <span class="relative z-10 flex items-center gap-2">
                                        <span>Request An Instant Quote</span>
                                        <i data-lucide="arrow-right" class="w-4 h-4"></i>
                                    </span>
                                    <div class="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                                </a>
                                <a href="services.html" class="px-7 py-4 rounded-xl border border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm active:scale-95 transition-all shadow-sm">
                                    Explore Our Services
                                </a>
                            </div>

                            <!-- Social Proof Strip -->
                            <div class="pt-4 flex items-center justify-center lg:justify-start gap-6 text-xs text-slate-500">
                                <div class="flex items-center gap-1.5">
                                    <span class="text-amber-500 font-bold text-base">★★★★★</span>
                                    <span class="font-bold text-slate-800">4.9 / 5 Rating</span>
                                </div>
                                <span class="text-slate-300">|</span>
                                <div>Over <strong class="text-slate-900 font-bold">150+ Happy Clients</strong> in {location}</div>
                            </div>
                        </div>

                        <!-- Hero Feature Card -->
                        <div class="lg:col-span-5" data-aos="fade-left" data-aos-delay="200">
                            <div class="relative mx-auto max-w-md rounded-3xl border border-slate-200/80 bg-white/95 p-8 shadow-2xl backdrop-blur-md">
                                <div class="space-y-5">
                                    <div class="flex items-center justify-between border-b border-slate-100 pb-4">
                                        <span class="text-xs font-bold uppercase tracking-wider text-primary-600 flex items-center gap-1.5">
                                            <i data-lucide="shield-check" class="w-4 h-4 text-primary-600"></i>
                                            Why Choose Us
                                        </span>
                                        <span class="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-600 border border-emerald-200">
                                            ● Verified Pro
                                        </span>
                                    </div>
                                    <div class="space-y-4">
                                        <div class="flex items-start gap-3">
                                            <div class="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm flex-shrink-0">
                                                <i data-lucide="check" class="w-4 h-4"></i>
                                            </div>
                                            <div>
                                                <h4 class="text-sm font-bold text-slate-900">Upfront Line-Item Estimates</h4>
                                                <p class="text-xs text-slate-500 mt-0.5">Transparent proposals with guaranteed zero hidden change orders.</p>
                                            </div>
                                        </div>
                                        <div class="flex items-start gap-3">
                                            <div class="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm flex-shrink-0">
                                                <i data-lucide="star" class="w-4 h-4"></i>
                                            </div>
                                            <div>
                                                <h4 class="text-sm font-bold text-slate-900">Master Craftsmanship</h4>
                                                <p class="text-xs text-slate-500 mt-0.5">Licensed, insured local team using premier commercial materials.</p>
                                            </div>
                                        </div>
                                        <div class="flex items-start gap-3">
                                            <div class="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm flex-shrink-0">
                                                <i data-lucide="heart-handshake" class="w-4 h-4"></i>
                                            </div>
                                            <div>
                                                <h4 class="text-sm font-bold text-slate-900">100% Satisfaction Pledge</h4>
                                                <p class="text-xs text-slate-500 mt-0.5">Final walkthrough with our lead specialist before signoff.</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="pt-2">
                                        <a href="#quick-booking" class="block w-full py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-center text-xs font-bold text-white shadow-md transition-colors">
                                            Quick Booking Form ↓
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Trust Proof Strip -->
            <section class="border-y border-slate-200 bg-white py-8" data-aos="fade-up">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                        <div class="space-y-1">
                            <div class="text-2xl sm:text-3xl font-black text-slate-900">100%</div>
                            <div class="text-xs text-slate-500 font-medium">Satisfaction Guarantee</div>
                        </div>
                        <div class="space-y-1">
                            <div class="text-2xl sm:text-3xl font-black text-primary-600">24/7</div>
                            <div class="text-xs text-slate-500 font-medium">Direct Support</div>
                        </div>
                        <div class="space-y-1">
                            <div class="text-2xl sm:text-3xl font-black text-slate-900">10+ Yrs</div>
                            <div class="text-xs text-slate-500 font-medium">Local Footprint in {location}</div>
                        </div>
                        <div class="space-y-1">
                            <div class="text-2xl sm:text-3xl font-black text-primary-600">5-Star</div>
                            <div class="text-xs text-slate-500 font-medium">Average Google Rating</div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- MODERN BENTO-GRID SHOWCASE SECTION -->
            <section class="py-12" data-aos="fade-up">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
                    <div class="text-center max-w-2xl mx-auto space-y-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-primary-600">Excellence by Design</span>
                        <h2 class="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">The {business_name} Difference</h2>
                        <p class="text-sm text-slate-600">Everything designed around reliability, transparent pricing, and effortless bookings.</p>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <!-- Bento Tile 1: Large Feature (2-cols) -->
                        <div class="md:col-span-2 rounded-3xl border border-slate-200 bg-gradient-to-br from-white via-primary-50/30 to-white p-8 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
                            <div class="space-y-4">
                                <div class="inline-flex items-center gap-2 rounded-xl bg-primary-100/80 px-3 py-1.5 text-xs font-bold text-primary-700">
                                    <i data-lucide="flame" class="w-4 h-4 text-primary-600"></i>
                                    #1 Rated in {location}
                                </div>
                                <h3 class="text-2xl font-bold text-slate-900">High-Impact Quality Tailored for {industry}</h3>
                                <p class="text-sm text-slate-600 leading-relaxed max-w-xl">
                                    We combine cutting-edge methodologies with seasoned local expertise. Every client receives direct attention from seasoned specialists, ensuring prompt completion and flawless results.
                                </p>
                            </div>
                            <div class="pt-6 grid grid-cols-3 gap-4 border-t border-slate-200/60 mt-6">
                                <div>
                                    <div class="text-xl font-bold text-slate-900">4.9★</div>
                                    <div class="text-[11px] text-slate-500">Google Reputation</div>
                                </div>
                                <div>
                                    <div class="text-xl font-bold text-primary-600">&lt;24h</div>
                                    <div class="text-[11px] text-slate-500">Response Window</div>
                                </div>
                                <div>
                                    <div class="text-xl font-bold text-slate-900">Zero</div>
                                    <div class="text-[11px] text-slate-500">Hidden Fees</div>
                                </div>
                            </div>
                        </div>

                        <!-- Bento Tile 2: Instant Booking (1-col) -->
                        <div class="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
                            <div class="space-y-4">
                                <div class="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                                    <i data-lucide="calendar" class="w-6 h-6"></i>
                                </div>
                                <h3 class="text-lg font-bold text-slate-900">Instant Online Bookings</h3>
                                <p class="text-xs text-slate-600 leading-relaxed">
                                    Schedule consultations and service visits right from your phone without waiting on back-and-forth phone tag.
                                </p>
                            </div>
                            <div class="pt-6">
                                <a href="#quick-booking" class="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-600 hover:text-emerald-700">
                                    <span>Reserve Next Slot</span>
                                    <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
                                </a>
                            </div>
                        </div>

                        <!-- Bento Tile 3: Warranty Guarantee (1-col) -->
                        <div class="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
                            <div class="space-y-4">
                                <div class="w-12 h-12 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center">
                                    <i data-lucide="shield" class="w-6 h-6"></i>
                                </div>
                                <h3 class="text-lg font-bold text-slate-900">Fully Licensed & Insured</h3>
                                <p class="text-xs text-slate-600 leading-relaxed">
                                    Complete peace of mind backed by comprehensive liability coverage and master craftsmanship warranties.
                                </p>
                            </div>
                            <div class="pt-6">
                                <span class="inline-flex items-center gap-1 text-[11px] font-semibold text-primary-700 bg-primary-50 px-2.5 py-1 rounded-full">
                                    ✓ 100% Guaranteed Work
                                </span>
                            </div>
                        </div>

                        <!-- Bento Tile 4: Client Satisfaction Excerpt (2-cols) -->
                        <div class="md:col-span-2 rounded-3xl border border-slate-200 bg-slate-900 text-white p-8 shadow-sm flex flex-col justify-between">
                            <div class="space-y-3">
                                <div class="flex items-center gap-1 text-amber-400 text-sm">
                                    ★★★★★ <span class="text-xs text-slate-400 font-semibold ml-2">Verified Client Testimony</span>
                                </div>
                                <blockquote class="text-base sm:text-lg font-medium text-slate-200 leading-relaxed italic">
                                    "Working with {business_name} was effortless. Their communication was punctual and the quality surpassed every expectation. Best in {location}!"
                                </blockquote>
                            </div>
                            <div class="pt-4 flex items-center justify-between border-t border-slate-800 mt-4 text-xs text-slate-400">
                                <span>Verified Customer in {location}</span>
                                <span class="text-primary-400 font-bold">5.0 Star Experience</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Featured Services Section -->
            <section class="py-12 bg-slate-50/80 border-y border-slate-200" data-aos="fade-up">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
                    <div class="text-center max-w-2xl mx-auto space-y-3" data-aos="fade-up">
                        <span class="text-xs font-bold uppercase tracking-wider text-primary-600">Our Core Capabilities</span>
                        <h2 class="text-3xl font-extrabold text-slate-900">Services Tailored for Maximum Value</h2>
                        <p class="text-sm text-slate-600">Designed to meet the exact standards of clients throughout {location}.</p>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {services_cards_html}
                    </div>
                    <div class="text-center pt-4">
                        <a href="services.html" class="inline-flex items-center gap-2 font-bold text-sm text-primary-600 hover:text-primary-700">
                            <span>View All Services & Pricing Catalog</span>
                            <i data-lucide="arrow-right" class="w-4 h-4"></i>
                        </a>
                    </div>
                </div>
            </section>

            <!-- Testimonials Section -->
            <section class="py-12 bg-white" data-aos="fade-up">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
                    <div class="text-center max-w-2xl mx-auto space-y-3" data-aos="fade-up">
                        <span class="text-xs font-bold uppercase tracking-wider text-primary-600">Real Client Experiences</span>
                        <h2 class="text-3xl font-extrabold text-slate-900">Trusted Across {location}</h2>
                        <p class="text-sm text-slate-600">See what our customers have to say about working with {business_name}.</p>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {testimonials_html}
                    </div>
                </div>
            </section>

            <!-- QUICK BOOKING FORM SECTION -->
            <section id="quick-booking" class="py-16 bg-gradient-to-b from-slate-50 to-white" data-aos="fade-up">
                <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="rounded-3xl border border-slate-200 bg-white p-8 sm:p-12 shadow-xl space-y-8">
                        <div class="text-center space-y-2">
                            <span class="inline-flex items-center gap-1.5 rounded-full bg-primary-100 text-primary-800 px-3 py-1 text-xs font-bold">
                                <i data-lucide="clock" class="w-3.5 h-3.5"></i> 60-Second Booking
                            </span>
                            <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900">Schedule Your Consultation Online</h2>
                            <p class="text-xs sm:text-sm text-slate-500">Pick your preferred service and time. Our team in {location} will confirm immediately.</p>
                        </div>

                        <form id="quick-booking-form" onsubmit="event.preventDefault(); document.getElementById('booking-success-msg').classList.remove('hidden'); this.reset();" class="space-y-4">
                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-xs font-bold text-slate-700 mb-1">Your Full Name</label>
                                    <input type="text" required placeholder="e.g. Michael Smith" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs sm:text-sm text-slate-900 outline-none focus:border-primary-600 focus:bg-white transition-colors" />
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-slate-700 mb-1">Phone or WhatsApp</label>
                                    <input type="tel" required placeholder="e.g. {phone or '(555) 000-0000'}" class="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs sm:text-sm text-slate-900 outline-none focus:border-primary-600 focus:bg-white transition-colors" />
                                </div>
                            </div>

                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-xs font-bold text-slate-700 mb-1">Service Inquired</label>
                                    <select class="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs sm:text-sm text-slate-900 outline-none focus:border-primary-600 focus:bg-white transition-colors">
                                        <option>Standard {industry} Consultation</option>
                                        <option>Express Assessment & Estimate</option>
                                        <option>Custom Project Inquiry</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-xs font-bold text-slate-700 mb-1">Preferred Timeline</label>
                                    <select class="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs sm:text-sm text-slate-900 outline-none focus:border-primary-600 focus:bg-white transition-colors">
                                        <option>This Week (Urgent)</option>
                                        <option>Within Next 14 Days</option>
                                        <option>Flexible / Planning Ahead</option>
                                    </select>
                                </div>
                            </div>

                            <button type="submit" class="w-full py-4 rounded-xl bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 text-white font-bold text-sm shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:shadow-[0_0_30px_rgba(99,102,241,0.6)] active:scale-95 transition-all flex items-center justify-center gap-2">
                                <span>Confirm Appointment Request</span>
                                <i data-lucide="check-circle" class="w-4 h-4"></i>
                            </button>
                        </form>

                        <div id="booking-success-msg" class="hidden rounded-2xl bg-emerald-50 border border-emerald-200 p-4 text-center text-xs font-semibold text-emerald-800 animate-in fade-in">
                            ✓ Thank you! Your booking request has been received. Our {location} specialist will text or call you to confirm your slot.
                        </div>
                    </div>
                </div>
            </section>

            <!-- Call to Action Banner -->
            <section class="py-16 bg-gradient-to-r from-primary-700 via-primary-600 to-indigo-800 text-white" data-aos="fade-up">
                <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
                    <h2 class="text-3xl sm:text-4xl font-extrabold tracking-tight">{content.get("cta_headline")}</h2>
                    <p class="text-base text-primary-100 max-w-2xl mx-auto">{content.get("cta_subheadline")}</p>
                    <div class="pt-4 flex flex-wrap justify-center gap-4">
                        <a href="contact.html" class="px-8 py-3.5 rounded-xl bg-white hover:bg-slate-100 text-primary-700 font-bold text-sm shadow-xl active:scale-95 transition-all">
                            Book Free Consultation
                        </a>
                        <a href="tel:{phone or '(555) 234-5678'}" class="px-8 py-3.5 rounded-xl border border-white/30 hover:bg-white/10 text-white font-semibold text-sm active:scale-95 transition-all">
                            Call {phone or '(555) 234-5678'}
                        </a>
                    </div>
                </div>
            </section>
        </main>

        {footer}
</body>
</html>
        '''
        return body

    def generate_about_page(
        self,
        business_name: str,
        industry: str,
        location: str,
        phone: Optional[str],
        email: Optional[str],
        content: Dict[str, Any],
        theme: Dict[str, str],
        theme_id: str
    ) -> str:
        """Generates engaging about.html page detailing story, core values, and standards."""
        head = self._render_head(f"About Us", business_name, theme)
        nav = self._render_nav(business_name, phone, "about.html", theme_id)
        footer = self._render_footer(business_name, location, phone, email, industry)

        values_html = ""
        for idx, val in enumerate(content.get("core_values", []), 1):
            val_delay = idx * 100
            values_html += f'''
            <div data-aos="fade-up" data-aos-delay="{val_delay}" class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
                <div class="w-10 h-10 rounded-xl bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm mb-4">
                    0{idx}
                </div>
                <h3 class="text-base font-bold text-slate-900 mb-2">{val['title']}</h3>
                <p class="text-xs text-slate-600 leading-relaxed">{val['desc']}</p>
            </div>
            '''

        story_paragraphs = content.get("about_story", "").split("\n\n")
        story_html = "".join(f'<p class="text-slate-600 leading-relaxed text-sm">{p}</p>' for p in story_paragraphs if p.strip())

        body = f'''
        {head}
        {nav}

        <main class="flex-1">
            <!-- Header Banner -->
            <section class="bg-gradient-to-b from-primary-50/70 to-white py-16 border-b border-slate-200" data-aos="fade-up">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
                    <span class="text-xs font-bold uppercase tracking-wider text-primary-600">Our Story & Commitment</span>
                    <h1 class="text-4xl font-extrabold text-slate-900 tracking-tight">About {business_name}</h1>
                    <p class="text-base text-slate-600 max-w-2xl mx-auto">
                        Dedicated to excellence in {industry}, proudly serving clients throughout {location}.
                    </p>
                </div>
            </section>

            <!-- Story Section -->
            <section class="py-16 bg-white" data-aos="fade-up">
                <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
                    <div class="space-y-4 text-justify">
                        {story_html}
                    </div>

                    <div class="rounded-2xl border border-primary-100 bg-primary-50/50 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div>
                            <h4 class="font-bold text-slate-900 text-sm">Need advice on an upcoming project?</h4>
                            <p class="text-xs text-slate-600 mt-0.5">Our senior specialists in {location} are happy to share complimentary insights.</p>
                        </div>
                        <a href="contact.html" class="px-5 py-2.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white font-semibold text-xs whitespace-nowrap">
                            Contact Our Team
                        </a>
                    </div>
                </div>
            </section>

            <!-- Core Values -->
            <section class="py-16 bg-slate-50 border-t border-slate-200" data-aos="fade-up">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
                    <div class="text-center max-w-2xl mx-auto space-y-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-primary-600">The Principles That Guide Us</span>
                        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900">Our Core Pillars of Excellence</h2>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {values_html}
                    </div>
                </div>
            </section>
        </main>

        {footer}
</body>
</html>
        '''
        return body

    def generate_services_page(
        self,
        business_name: str,
        industry: str,
        location: str,
        phone: Optional[str],
        email: Optional[str],
        content: Dict[str, Any],
        theme: Dict[str, str],
        theme_id: str
    ) -> str:
        """Generates comprehensive services.html page with pricing and process."""
        head = self._render_head(f"Services & Pricing", business_name, theme)
        nav = self._render_nav(business_name, phone, "services.html", theme_id)
        footer = self._render_footer(business_name, location, phone, email, industry)

        services_catalog_html = ""
        for idx, svc in enumerate(content.get("services", [])):
            features_html = "".join(
                f'<li class="flex items-center gap-2 text-xs text-slate-600"><span class="text-primary-600 font-bold">✓</span> {feat}</li>'
                for feat in svc.get("features", [])
            )
            svc_delay = (idx % 2 + 1) * 150
            services_catalog_html += f'''
            <div data-aos="fade-up" data-aos-delay="{svc_delay}" class="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm hover:shadow-lg transition-all flex flex-col justify-between">
                <div class="space-y-4">
                    <div class="flex items-center justify-between gap-3">
                        <h3 class="text-lg font-bold text-slate-900">{svc['title']}</h3>
                        <span class="rounded-full bg-primary-50 text-primary-700 px-3 py-1 text-xs font-bold">{svc.get('price_hint', 'Custom')}</span>
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">{svc['description']}</p>
                    <div class="pt-3 border-t border-slate-100">
                        <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">What is included:</span>
                        <ul class="space-y-2">
                            {features_html}
                        </ul>
                    </div>
                </div>
                <div class="pt-6">
                    <a href="contact.html" class="block w-full py-2.5 rounded-xl bg-slate-900 hover:bg-primary-600 text-white font-semibold text-xs text-center transition-colors">
                        Request This Service →
                    </a>
                </div>
            </div>
            '''

        faqs_html = ""
        for idx, faq in enumerate(content.get("faqs", []), 1):
            faqs_html += f'''
            <div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-2">
                <h4 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <span class="text-primary-600 font-extrabold">Q:</span>
                    <span>{faq['question']}</span>
                </h4>
                <p class="text-xs text-slate-600 leading-relaxed pl-6">{faq['answer']}</p>
            </div>
            '''

        body = f'''
        {head}
        {nav}

        <main class="flex-1">
            <!-- Header Banner -->
            <section class="bg-gradient-to-b from-primary-50/70 to-white py-16 border-b border-slate-200">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
                    <span class="text-xs font-bold uppercase tracking-wider text-primary-600">Full Capabilities & Offerings</span>
                    <h1 class="text-4xl font-extrabold text-slate-900 tracking-tight">Our Services Catalog</h1>
                    <p class="text-base text-slate-600 max-w-2xl mx-auto">
                        Transparent, competitive pricing and master-grade solutions for {industry} in {location}.
                    </p>
                </div>
            </section>

            <!-- Catalog Grid -->
            <section class="py-16 bg-slate-50">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {services_catalog_html}
                    </div>
                </div>
            </section>

            <!-- 4-Step Process Section -->
            <section class="py-16 bg-white border-t border-slate-200">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
                    <div class="text-center max-w-2xl mx-auto space-y-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-primary-600">How We Work</span>
                        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900">Our 4-Step Seamless Process</h2>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-center">
                        <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100">
                            <div class="w-10 h-10 rounded-full bg-primary-600 text-white font-bold flex items-center justify-center mx-auto mb-3">1</div>
                            <h4 class="font-bold text-sm text-slate-900">Free Consultation</h4>
                            <p class="text-xs text-slate-500 mt-1">We listen to your specific needs and evaluate your requirements.</p>
                        </div>
                        <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100">
                            <div class="w-10 h-10 rounded-full bg-primary-600 text-white font-bold flex items-center justify-center mx-auto mb-3">2</div>
                            <h4 class="font-bold text-sm text-slate-900">Transparent Quote</h4>
                            <p class="text-xs text-slate-500 mt-1">Detailed proposal with timeline, materials, and fixed pricing.</p>
                        </div>
                        <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100">
                            <div class="w-10 h-10 rounded-full bg-primary-600 text-white font-bold flex items-center justify-center mx-auto mb-3">3</div>
                            <h4 class="font-bold text-sm text-slate-900">Master Execution</h4>
                            <p class="text-xs text-slate-500 mt-1">Our certified specialists execute the work with clean daily progress.</p>
                        </div>
                        <div class="p-6 rounded-2xl bg-slate-50 border border-slate-100">
                            <div class="w-10 h-10 rounded-full bg-primary-600 text-white font-bold flex items-center justify-center mx-auto mb-3">4</div>
                            <h4 class="font-bold text-sm text-slate-900">100% Sign-Off</h4>
                            <p class="text-xs text-slate-500 mt-1">Final walkthrough ensuring every specification is fully satisfied.</p>
                        </div>
                    </div>
                </div>
            </section>

            <!-- FAQ Section -->
            <section class="py-16 bg-slate-50 border-t border-slate-200">
                <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
                    <div class="text-center space-y-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-primary-600">Common Questions</span>
                        <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900">Frequently Asked Questions</h2>
                    </div>
                    <div class="space-y-4">
                        {faqs_html}
                    </div>
                </div>
            </section>
        </main>

        {footer}
</body>
</html>
        '''
        return body

    def generate_contact_page(
        self,
        business_name: str,
        industry: str,
        location: str,
        phone: Optional[str],
        email: Optional[str],
        content: Dict[str, Any],
        theme: Dict[str, str],
        theme_id: str
    ) -> str:
        """Generates interactive contact.html page with functional booking form & JS modal."""
        head = self._render_head(f"Contact & Booking", business_name, theme)
        nav = self._render_nav(business_name, phone, "contact.html", theme_id)
        footer = self._render_footer(business_name, location, phone, email, industry)

        phone_val = phone or "(555) 234-5678"
        email_val = email or f"contact@{re.sub(r'[^a-zA-Z0-9]', '', business_name.lower())}.com"

        service_options_html = ""
        for svc in content.get("services", []):
            service_options_html += f'<option value="{svc["title"]}">{svc["title"]} ({svc.get("price_hint", "")})</option>\n'

        body = f'''
        {head}
        {nav}

        <main class="flex-1">
            <!-- Header Banner -->
            <section class="bg-gradient-to-b from-primary-50/70 to-white py-16 border-b border-slate-200">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
                    <span class="text-xs font-bold uppercase tracking-wider text-primary-600">Get In Touch</span>
                    <h1 class="text-4xl font-extrabold text-slate-900 tracking-tight">Schedule Your Service or Consultation</h1>
                    <p class="text-base text-slate-600 max-w-2xl mx-auto">
                        Fast response guaranteed. Reach out directly or complete the brief request form below.
                    </p>
                </div>
            </section>

            <!-- Two-Column Contact & Form Section -->
            <section class="py-16 bg-white">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
                        <!-- Direct Contact Cards -->
                        <div class="lg:col-span-5 space-y-6" data-aos="fade-right">
                            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-6 space-y-4">
                                <h3 class="text-base font-bold text-slate-900 border-b border-slate-200 pb-3">Direct Contact Channels</h3>
                                <div class="space-y-4 text-xs">
                                    <div class="flex items-start gap-3">
                                        <div class="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm flex-shrink-0">📞</div>
                                        <div>
                                            <span class="text-slate-500 font-semibold block">Phone</span>
                                            <a href="tel:{phone_val}" class="text-sm font-bold text-slate-900 hover:text-primary-600">{phone_val}</a>
                                            <span class="text-[11px] text-slate-400 block mt-0.5">Mon - Sat: 8:00 AM - 6:00 PM</span>
                                        </div>
                                    </div>
                                    <div class="flex items-start gap-3">
                                        <div class="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm flex-shrink-0">✉️</div>
                                        <div>
                                            <span class="text-slate-500 font-semibold block">Email</span>
                                            <a href="mailto:{email_val}" class="text-sm font-bold text-slate-900 hover:text-primary-600">{email_val}</a>
                                            <span class="text-[11px] text-slate-400 block mt-0.5">Average response under 2 hours</span>
                                        </div>
                                    </div>
                                    <div class="flex items-start gap-3">
                                        <div class="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm flex-shrink-0">📍</div>
                                        <div>
                                            <span class="text-slate-500 font-semibold block">Service Area</span>
                                            <span class="text-sm font-bold text-slate-900">{location}</span>
                                            <span class="text-[11px] text-slate-400 block mt-0.5">Serving all surrounding municipal districts</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Styled Map Representation Card -->
                            <div class="rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
                                <div class="bg-slate-800 p-6 text-white text-center space-y-2">
                                    <span class="text-xs uppercase font-semibold tracking-wider text-primary-400">Local Presence</span>
                                    <h4 class="text-base font-bold">{location} Service Hub</h4>
                                    <p class="text-xs text-slate-400">Centrally located for rapid emergency response and scheduled on-site appointments.</p>
                                </div>
                                <div class="bg-slate-100 p-4 text-center text-xs text-slate-500 font-mono">
                                    🗺️ Interactive GPS Navigation & Field Dispatch Map
                                </div>
                            </div>
                        </div>

                        <!-- Interactive Form -->
                        <div class="lg:col-span-7" data-aos="fade-left">
                            <div class="rounded-3xl border border-slate-200 bg-white p-8 shadow-xl">
                                <h3 class="text-xl font-bold text-slate-900 mb-1">Request a Consultation / Estimate</h3>
                                <p class="text-xs text-slate-500 mb-6">Fill in your project details and our team will get in touch within 2 business hours.</p>

                                <form id="booking-form" class="space-y-4">
                                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <div>
                                            <label class="block text-xs font-semibold text-slate-700 mb-1">Your Full Name *</label>
                                            <input type="text" id="client-name" required placeholder="John Doe" class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-primary-600 focus:ring-1 focus:ring-primary-600 outline-none">
                                        </div>
                                        <div>
                                            <label class="block text-xs font-semibold text-slate-700 mb-1">Phone Number *</label>
                                            <input type="tel" id="client-phone" required placeholder="(555) 000-0000" class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-primary-600 focus:ring-1 focus:ring-primary-600 outline-none">
                                        </div>
                                    </div>

                                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <div>
                                            <label class="block text-xs font-semibold text-slate-700 mb-1">Email Address *</label>
                                            <input type="email" id="client-email" required placeholder="john@example.com" class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-primary-600 focus:ring-1 focus:ring-primary-600 outline-none">
                                        </div>
                                        <div>
                                            <label class="block text-xs font-semibold text-slate-700 mb-1">Service Requested *</label>
                                            <select id="client-service" class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-xs text-slate-900 bg-white focus:border-primary-600 focus:ring-1 focus:ring-primary-600 outline-none">
                                                {service_options_html}
                                                <option value="General Inquiry">General Question / Other</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div>
                                        <label class="block text-xs font-semibold text-slate-700 mb-1">Preferred Time / Timeline</label>
                                        <select id="client-timeline" class="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-xs text-slate-900 bg-white focus:border-primary-600 focus:ring-1 focus:ring-primary-600 outline-none">
                                            <option value="Immediately (Urgent)">Immediately (Urgent / Next 24 Hours)</option>
                                            <option value="Within 1-2 Weeks">Within 1 - 2 Weeks</option>
                                            <option value="This Month">Sometime this month</option>
                                            <option value="Planning Stage">Just researching / Planning stage</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label class="block text-xs font-semibold text-slate-700 mb-1">Project Details or Notes</label>
                                        <textarea id="client-notes" rows="4" placeholder="Briefly describe what you're looking to achieve..." class="w-full rounded-xl border border-slate-300 p-3.5 text-xs text-slate-900 placeholder-slate-400 focus:border-primary-600 focus:ring-1 focus:ring-primary-600 outline-none"></textarea>
                                    </div>

                                    <div class="pt-2">
                                        <button type="submit" class="w-full py-3.5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white font-bold text-sm shadow-lg shadow-primary-600/25 active:scale-95 transition-all">
                                            Submit Booking Request →
                                        </button>
                                        <p class="text-[11px] text-slate-400 text-center mt-2.5">
                                            🔒 Your details are safe with {business_name}. Never shared with third parties.
                                        </p>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <!-- Interactive Success Modal -->
        <div id="success-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm hidden items-center justify-center p-4">
            <div class="relative w-full max-w-md rounded-2xl bg-white p-7 text-center shadow-2xl space-y-4">
                <div class="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 mx-auto flex items-center justify-center text-2xl font-bold">
                    ✓
                </div>
                <h3 class="text-xl font-bold text-slate-900">Booking Request Received!</h3>
                <p id="success-message" class="text-xs text-slate-600 leading-relaxed">
                    Thank you! The team at {business_name} has received your inquiry and will reach out shortly.
                </p>
                <div class="pt-3">
                    <button id="close-modal-btn" class="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs">
                        Back to Website
                    </button>
                </div>
            </div>
        </div>

        <script>
            const form = document.getElementById('booking-form');
            const modal = document.getElementById('success-modal');
            const closeBtn = document.getElementById('close-modal-btn');
            const successMsg = document.getElementById('success-message');

            if (form) {{
                form.addEventListener('submit', (e) => {{
                    e.preventDefault();
                    const name = document.getElementById('client-name').value || 'valued client';
                    const service = document.getElementById('client-service').value || 'service';
                    if (successMsg) {{
                        successMsg.innerText = `Thank you, ${{name}}! Your request for "${{service}}" has been confirmed. Our team will contact you within 2 hours.`;
                    }}
                    if (modal) {{
                        modal.classList.remove('hidden');
                        modal.classList.add('flex');
                    }}
                    form.reset();
                }});
            }}

            if (closeBtn && modal) {{
                closeBtn.addEventListener('click', () => {{
                    modal.classList.add('hidden');
                    modal.classList.remove('flex');
                }});
            }}
        </script>

        {footer}
</body>
</html>
        '''
        return body

    def generate_multi_page_demo(
        self,
        lead: Lead,
        db: Session,
        custom_instructions: Optional[str] = None,
        theme_color: Optional[str] = None
    ) -> DemoGenerateResponse:
        """
        Creates a complete multi-page HTML prototype with Tailwind CSS:
        - Writes index.html, about.html, services.html, contact.html to static/demos/{lead_id}/
        - Updates Lead record in DB with demo_url & demo_preview_html
        - Advances status to 'demo_generated' if in early pipeline
        """
        business_name = lead.business_name
        industry = lead.industry or "General Business"
        location = lead.location or "Local Area"
        phone = lead.phone
        email = lead.email

        # 1. Resolve Theme
        theme_id = self.resolve_theme(industry=industry, preferred_theme=theme_color)
        theme = COLOR_THEMES.get(theme_id, COLOR_THEMES["indigo"])

        # 2. Generate Content (Gemini with Fallback)
        content = self._generate_gemini_content(
            business_name=business_name,
            industry=industry,
            location=location,
            notes=lead.notes or "",
            custom_instructions=custom_instructions
        )

        if not content:
            content = self._get_fallback_content(
                business_name=business_name,
                industry=industry,
                location=location,
                custom_instructions=custom_instructions
            )

        # 3. Generate HTML Pages
        index_html = self.generate_index_page(
            business_name=business_name,
            industry=industry,
            location=location,
            phone=phone,
            email=email,
            content=content,
            theme=theme,
            theme_id=theme_id
        )

        about_html = self.generate_about_page(
            business_name=business_name,
            industry=industry,
            location=location,
            phone=phone,
            email=email,
            content=content,
            theme=theme,
            theme_id=theme_id
        )

        services_html = self.generate_services_page(
            business_name=business_name,
            industry=industry,
            location=location,
            phone=phone,
            email=email,
            content=content,
            theme=theme,
            theme_id=theme_id
        )

        contact_html = self.generate_contact_page(
            business_name=business_name,
            industry=industry,
            location=location,
            phone=phone,
            email=email,
            content=content,
            theme=theme,
            theme_id=theme_id
        )

        # 4. Save to Disk under static/demos/{lead_id}/
        lead_dir = os.path.join(DEMOS_STORAGE_DIR, str(lead.id))
        os.makedirs(lead_dir, exist_ok=True)

        pages = {
            "index.html": index_html,
            "about.html": about_html,
            "services.html": services_html,
            "contact.html": contact_html,
        }

        for fname, markup in pages.items():
            fpath = os.path.join(lead_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(markup)

        # Write manifest
        manifest = {
            "lead_id": lead.id,
            "business_name": business_name,
            "industry": industry,
            "location": location,
            "theme": theme_id,
            "pages": list(pages.keys())
        }
        with open(os.path.join(lead_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 5. Formulate Hosted Demo URL
        port = settings.BACKEND_PORT
        demo_url = f"http://localhost:{port}/demos/{lead.id}/"

        # 6. Persist to Database
        update_fields: Dict[str, Any] = {
            "demo_url": demo_url,
            "demo_preview_html": index_html,
        }
        if lead.status in ["new", "analyzed", "scored", "outreach_generated"]:
            update_fields["status"] = "demo_generated"

        crud_lead.update(db, db_obj=lead, obj_in=update_fields)

        preview_snippet = f"{content.get('hero_headline', '')} — {len(pages)} Multi-page Tailwind site created"

        return DemoGenerateResponse(
            success=True,
            lead_id=lead.id,
            demo_url=demo_url,
            business_name=business_name,
            industry=industry,
            message=f"Multi-page website demo generated successfully with {len(pages)} responsive pages (Home, About, Services, Contact)!",
            preview_snippet=preview_snippet,
            pages_generated=list(pages.keys())
        )

    def get_demo_pages(self, lead_id: int) -> Dict[str, str]:
        """Retrieves generated HTML pages for a given lead from disk."""
        lead_dir = os.path.join(DEMOS_STORAGE_DIR, str(lead_id))
        result = {}
        if not os.path.exists(lead_dir):
            return result

        for fname in ["index.html", "about.html", "services.html", "contact.html"]:
            fpath = os.path.join(lead_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        result[fname] = f.read()
                except Exception as e:
                    logger.error(f"Error reading {fpath}: {e}")

        return result


# Singleton instance
demo_generator = WebsiteDemoGenerator()
