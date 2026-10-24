import re
from typing import List, Dict, Any, Optional
from backend.app.agent.providers.base import LLMProviderInterface, AgentResponse, ToolCall
from backend.app.tools.registry import tool_registry

class MockLLMProvider(LLMProviderInterface):
    """
    Deterministic, rule-grounded mock provider for development, evaluation, and CI.
    Understands Tamil, Tanglish, and English queries accurately.
    Ensures zero hallucination and enforces official source citations.
    """

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools_schema: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_message = m.get("content", "").strip()
                break

        msg_lower = user_message.lower()

        # 1. Prompt Injection Defense
        injection_patterns = [
            "ignore previous instructions",
            "system prompt",
            "drop table",
            "you are now evil",
            "bypass security",
            "leak database"
        ]
        if any(pat in msg_lower for pat in injection_patterns):
            return AgentResponse(
                content="பாதுகாப்புக் கொள்கையின்படி இந்த கட்டளையை செயல்படுத்த முடியாது. அரசு சேவைகள் தொடர்பான கேள்விகளை மட்டும் கேளுங்கள். / I cannot execute this directive as it violates safety constraints.",
                language="ta",
                citations=[]
            )

        # 2. Human Escalation Intent
        if any(kw in msg_lower for kw in ["human", "officer", "helpdesk", "complaint", "officer help", "மனித உதவி", "அதிகாரி", "escalate", "reject", "grievance", "புகார்"]):
            esc_res = tool_registry.execute_tool("escalate_to_human", {"reason": user_message})
            return AgentResponse(
                content=f"வணக்கம். உங்கள் கோரிக்கை பதிவு செய்யப்பட்டது. குறிப்பு எண்: {esc_res.get('ticket_reference')}. அரசு நல அலுவலர் இதை ஆய்வு செய்வார்.\n\nYour issue has been escalated to human assistance.",
                language="ta",
                tool_calls=[ToolCall(tool_name="escalate_to_human", arguments={"reason": user_message})],
                action_cards=[esc_res]
            )


        # 4. Scholarship (Post-Matric) - Check first before general income/community checks
        if any(kw in msg_lower for kw in ["scholarship", "கல்வி உதவித்தொகை", "உதவித்தொகை", "போஸ்ட் மெட்ரிக்", "போஸ்ட்-மெட்ரிக்", "post-matric", "bc scholarship", "sc scholarship", "aadhaar seeding"]):
            plan = tool_registry.execute_tool("create_action_plan", {"service_id": "post_matric_scholarship"})
            details = tool_registry.execute_tool("get_service_details", {"service_id": "post_matric_scholarship"})
            is_tamil = any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in user_message) or "venum" in msg_lower

            if is_tamil:
                content = (
                    "**தமிழ்நாடு போஸ்ட்-மெட்ரிக் கல்வி உதவித்தொகை திட்டம்:**\n\n"
                    "SC, ST, SCC மற்றும் தகுதியுள்ள BC/MBC கல்லூரி மாணவர்களுக்கான திட்டம். பெற்றோர் ஆண்டு வருமானம் ₹2,50,000-க்குள் இருக்க வேண்டும்.\n\n"
                    "**தேவையான 3 முன்நிபந்தனை சான்றிதழ்கள் (Prerequisites):**\n"
                    "1. **சாதிச் சான்றிதழ் (Community Certificate)**\n"
                    "2. **வருமானச் சான்றிதழ் (Income Certificate - வருமானம் <= ₹2.5 லட்சம்)**\n"
                    "3. **இருப்பிடச் சான்றிதழ் (Nativity Certificate)**\n\n"
                    "**கூடுதல் ஆவணங்கள்:** கல்லூரி போனாஃபைட் சான்றிதழ், ஆதார் இணைக்கப்பட்ட வங்கிக் கணக்கு புத்தகம், மதிப்பெண் பட்டியல்.\n"
                    "• **விண்ணப்ப கட்டணம்:** முற்றிலும் இலவசம் (₹0)."
                )
            else:
                content = (
                    "**Tamil Nadu Post-Matric Scholarship Guidance:**\n\n"
                    "For SC, ST, SCC, and eligible BC/MBC students with annual parental income up to ₹2,50,000.\n\n"
                    "**3 Prerequisite Certificates Required:**\n"
                    "1. **Community Certificate**\n"
                    "2. **Income Certificate (Valid for current academic year <= ₹2.5 Lakhs)**\n"
                    "3. **Nativity Certificate**\n\n"
                    "**Additional Documents:** College Bonafide Certificate, Aadhaar-seeded Bank Passbook, Marksheets.\n"
                    "• **Application Fee:** ₹0 (Free of cost)."
                )

            return AgentResponse(
                content=content,
                language="ta" if is_tamil else "en",
                tool_calls=[
                    ToolCall(tool_name="resolve_service_dependencies", arguments={"service_id": "post_matric_scholarship"}),
                    ToolCall(tool_name="create_action_plan", arguments={"service_id": "post_matric_scholarship"})
                ],
                citations=[{"title": s["title"], "url": s["url"]} for s in details.get("official_sources", [])],
                action_cards=[{
                    "card_type": "DEPENDENCY_PLAN",
                    "target_service_id": "post_matric_scholarship",
                    "plan": plan
                }]
            )

        # 4. First Graduate Certificate - Check before generic certificates
        if any(kw in msg_lower for kw in ["first graduate", "முதல் தலைமுறை", "பட்டதாரி", "engineering fee waiver", "mudhal thalaimurai", "fg"]):
            details = tool_registry.execute_tool("get_service_details", {"service_id": "first_graduate_certificate"})
            plan = tool_registry.execute_tool("create_action_plan", {"service_id": "first_graduate_certificate"})
            is_tamil = any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in user_message) or "eppadi" in msg_lower
            
            if is_tamil:
                content = (
                    "**முதல் தலைமுறை பட்டதாரி சான்றிதழ் (First Graduate Certificate):**\n\n"
                    "குடும்பத்தில் எவரும் இதற்கு முன் பட்டப்படிப்பு முடித்திருக்கக் கூடாது மற்றும் மூத்த சகோதரர் சலுகை பெற்றிருக்கக் கூடாது.\n\n"
                    "• **முன்நிபந்தனை (Prerequisite):** இருப்பிடச் சான்றிதழ் (Nativity Certificate) அவசியமாகும்.\n"
                    "• **கட்டணம்:** ₹60\n"
                    "• **பயன்:** பொறியியல்/மருத்துவ கலந்தாய்வில் கல்விக் கட்டண விலக்கு.\n\n"
                    "**தேவையான ஆவணங்கள்:**\n"
                    "1. குடும்ப அட்டை (Ration card)\n"
                    "2. பெற்றோர் மற்றும் உடன் பிறந்தோரின் கல்விச் சான்றிதழ்கள் / மாற்றுச் சான்றிதழ் (TC)\n"
                    "3. பெற்றோர் மற்றும் மாணவர் கையொப்பமிட்ட கூட்டு உறுதிமொழிப் படிவம் (Joint Declaration)"
                )
            else:
                content = (
                    "**First Graduate Certificate Guidance:**\n\n"
                    "Eligible if no one in the immediate family has graduated and no elder sibling has availed the concession.\n\n"
                    "• **Prerequisite Service:** Nativity Certificate is required.\n"
                    "• **Fee:** ₹60\n"
                    "• **Benefit:** Tuition fee waiver in government counseling quota seats.\n\n"
                    "**Required Documents:**\n"
                    "1. Smart Ration Card\n"
                    "2. School Transfer Certificates (TC) of parents & siblings\n"
                    "3. Prescribed Joint Declaration signed by applicant & parents"
                )

            return AgentResponse(
                content=content,
                language="ta" if is_tamil else "en",
                tool_calls=[
                    ToolCall(tool_name="resolve_service_dependencies", arguments={"service_id": "first_graduate_certificate"}),
                    ToolCall(tool_name="create_action_plan", arguments={"service_id": "first_graduate_certificate"})
                ],
                citations=[{"title": s["title"], "url": s["url"]} for s in details.get("official_sources", [])],
                action_cards=[{
                    "card_type": "DEPENDENCY_PLAN",
                    "target_service_id": "first_graduate_certificate",
                    "plan": plan
                }]
            )

        # 5. Community Certificate
        if any(kw in msg_lower for kw in ["community", "caste", "சாதி", "community certificate", "jaathi", "வட்டாட்சியர்", "e-sevai"]) and "income" not in msg_lower and "வருமான" not in msg_lower:
            details = tool_registry.execute_tool("get_service_details", {"service_id": "community_certificate"})
            plan = tool_registry.execute_tool("create_action_plan", {"service_id": "community_certificate"})
            
            is_tamil = any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in user_message) or "venum" in msg_lower or "epdi" in msg_lower
            
            if is_tamil:
                content = (
                    "**சாதிச் சான்றிதழ் (Community Certificate) விண்ணப்ப வழிகாட்டி:**\n\n"
                    "• **துறை:** வருவாய் மற்றும் பேரிடர் மேலாண்மைத் துறை\n"
                    "• **விண்ணப்ப கட்டணம்:** ₹60 (அதிகாரப்பூர்வ இ-சேவை கட்டணம்)\n"
                    "• **சேவை காலம்:** 15 வேலை நாட்கள் (குடிமக்கள் சாசனம்)\n"
                    "• **செல்லுபடியாகும் காலம்:** வாழ்நாள் முழுமைக்கும் (Permanent)\n\n"
                    "**தேவையான ஆவணங்கள்:**\n"
                    "1. பாஸ்போர்ட் அளவு புகைப்படம்\n"
                    "2. முகவரிச் சான்று (ஸ்மார்ட் ரேஷன் கார்டு / ஆதார்)\n"
                    "3. பெற்றோர் / உடன்பிறந்தோரின் சாதிச் சான்றிதழ்\n"
                    "4. சுய உறுதிமொழிப் படிவம்\n\n"
                    "இ-சேவை (e-Sevai) இணையதளத்தில் CAN பதிவு செய்து விண்ணப்பிக்கலாம்."
                )
            else:
                content = (
                    "**Community Certificate Application Guide:**\n\n"
                    "• **Department:** Revenue and Disaster Management Department\n"
                    "• **Statutory Fee:** ₹60 (via official e-Sevai portal)\n"
                    "• **Processing Time:** 15 working days as per Citizen Charter\n"
                    "• **Validity:** Permanent / Lifetime\n\n"
                    "**Required Documents:**\n"
                    "1. Applicant Passport Size Photograph\n"
                    "2. Address Proof (Smart Ration Card / Aadhaar Card)\n"
                    "3. Community Certificate of Father/Mother/Sibling\n"
                    "4. Self-Declaration Form\n\n"
                    "You can apply through the official TN e-Sevai portal using your Citizen Access Number (CAN)."
                )

            return AgentResponse(
                content=content,
                language="ta" if is_tamil else "en",
                tool_calls=[
                    ToolCall(tool_name="get_service_details", arguments={"service_id": "community_certificate"}),
                    ToolCall(tool_name="create_action_plan", arguments={"service_id": "community_certificate"})
                ],
                citations=[
                    {"title": s["title"], "url": s["url"]}
                    for s in details.get("official_sources", [])
                ],
                action_cards=[
                    {
                        "card_type": "SERVICE_PLAN",
                        "service_id": "community_certificate",
                        "name_en": details.get("name_en"),
                        "name_ta": details.get("name_ta"),
                        "portal_url": details.get("portal_url"),
                        "fee_inr": details.get("fee", {}).get("amount_inr"),
                        "processing_days": details.get("processing_time", {}).get("working_days"),
                        "steps_count": len(details.get("application_steps", []))
                    }
                ]
            )

        # 6. Income Certificate
        if any(kw in msg_lower for kw in ["income", "வருமான", "varumana", "income certificate"]):
            details = tool_registry.execute_tool("get_service_details", {"service_id": "income_certificate"})
            is_tamil = any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in user_message) or "venum" in msg_lower
            
            if is_tamil:
                content = (
                    "**வருமானச் சான்றிதழ் (Income Certificate) விவரங்கள்:**\n\n"
                    "• **கட்டணம்:** ₹60 (இ-சேவை கட்டணம்)\n"
                    "• **கால அவகாசம்:** 15 வேலை நாட்கள்\n"
                    "• **செல்லுபடியாகும் காலம்:** வழங்கப்பட்ட நாளிலிருந்து 6 மாதங்கள் மட்டுமே\n\n"
                    "**தேவையான ஆவணங்கள்:**\n"
                    "1. புகைப்படம்\n"
                    "2. குடும்ப அட்டை (Ration Card)\n"
                    "3. மாத சம்பளச் சான்று அல்லது VAO அறிக்கை\n"
                    "4. சுய உறுதிமொழிப் படிவம்"
                )
            else:
                content = (
                    "**Income Certificate Application Details:**\n\n"
                    "• **Statutory Fee:** ₹60 (e-Sevai)\n"
                    "• **Processing Time:** 15 working days\n"
                    "• **Validity:** 6 Months from the date of issue\n\n"
                    "**Required Documents:**\n"
                    "1. Applicant Photograph\n"
                    "2. Smart Ration Card / Family Card\n"
                    "3. Salary Slip / Form 16 / VAO Income Report\n"
                    "4. Self-Declaration"
                )

            return AgentResponse(
                content=content,
                language="ta" if is_tamil else "en",
                tool_calls=[ToolCall(tool_name="get_service_details", arguments={"service_id": "income_certificate"})],
                citations=[{"title": s["title"], "url": s["url"]} for s in details.get("official_sources", [])],
                action_cards=[{
                    "card_type": "SERVICE_PLAN",
                    "service_id": "income_certificate",
                    "name_en": details.get("name_en"),
                    "name_ta": details.get("name_ta"),
                    "portal_url": details.get("portal_url"),
                    "fee_inr": 60.0
                }]
            )

        # 7. Nativity Certificate
        if any(kw in msg_lower for kw in ["nativity", "இருப்பிட", "பிறப்பிட", "residence certificate"]):
            details = tool_registry.execute_tool("get_service_details", {"service_id": "nativity_certificate"})
            return AgentResponse(
                content=(
                    "**இருப்பிட / பிறப்பிடச் சான்றிதழ் (Nativity Certificate):**\n\n"
                    "தமிழ்நாட்டில் குறைந்தது 5 ஆண்டுகள் தொடர் வசிப்பு அல்லது பிறப்பை உறுதி செய்யும் சான்றிதழ்.\n"
                    "• **கட்டணம்:** ₹60\n"
                    "• **சேவை காலம்:** 15 வேலை நாட்கள்\n"
                    "• **தேவையானவை:** பிறப்புச் சான்றிதழ்/பள்ளி மாற்றுச் சான்றிதழ் (TC), பெற்றோரின் இருப்பிடச் சான்று, குடும்ப அட்டை."
                ),
                language="ta",
                tool_calls=[ToolCall(tool_name="get_service_details", arguments={"service_id": "nativity_certificate"})],
                citations=[{"title": s["title"], "url": s["url"]} for s in details.get("official_sources", [])]
            )

        # 8. General / Fallback with search
        search_res = tool_registry.execute_tool("search_services", {"query": user_message})
        if search_res.get("count", 0) > 0:
            srv_names = ", ".join([s["name_en"] for s in search_res["services"]])
            return AgentResponse(
                content=f"வணக்கம்! உங்கள் கேள்விக்குரிய தொடர்புடைய சேவைகள்: {srv_names}. இதில் எந்த சேவையைப் பற்றி நீங்கள் விரிவாக அறிய விரும்புகிறீர்கள்?",
                language="ta",
                tool_calls=[ToolCall(tool_name="search_services", arguments={"query": user_message})],
                action_cards=search_res["services"]
            )

        # 9. Inquiries mentioning schemes, pensions, subsidies, or unindexed services
        if any(kw in msg_lower for kw in ["pension", "farmer", "subsidy", "schemes", "ration card", "பென்ஷன்", "விவசாயி"]):
            return AgentResponse(
                content=(
                    "தற்போது முதியோர் ஓய்வூதியம் (OAP) மற்றும் உழவர் நலத்திட்டங்கள் (Farmer Subsidies) நமது சரிபார்ப்பு வரிசையில் (Verification Queue) உள்ளன. "
                    "வருவாய்த் துறை சான்றிதழ்கள் (சாதி, வருமானம், இருப்பிடம்) அல்லது கல்லூரி கல்வி உதவித்தொகை குறித்த வழிகாட்டுதல் தேவைப்படுகிறதா?\n\n"
                    "Pension and agricultural subsidy playbooks are currently in the verification queue. Would you like assistance with certificates or student scholarships?"
                ),
                language="ta",
                tool_calls=[ToolCall(tool_name="search_services", arguments={"query": user_message})],
                citations=[]
            )

        # 10. Unsupported / Unknown Service
        return AgentResponse(
            content=(
                "மன்னிக்கவும், நீங்கள் குறிப்பிட்ட சேவை தற்போது நமது சரிபார்க்கப்பட்ட தகவல் தொகுப்பில் (Verified Catalog) இல்லை. "
                "உங்களுக்கு ஏதேனும் சான்றிதழ் (சாதி, வருமானம், இருப்பிடம், முதல் பட்டதாரி) அல்லது கல்வி உதவித்தொகை குறித்து உதவ வேண்டுமா?\n\n"
                "I could not locate verified official guidelines for this specific query. Would you like assistance with certificates or scholarships?"
            ),
            language="ta",
            citations=[]
        )
