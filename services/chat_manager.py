from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from services.llm_factory import LLMFactory
from services.analytics_service import AnalyticsService

class ChatManager:
    def __init__(self):
        # We store history in memory mapping session_ids to message arrays
        self.sessions = {}

    def get_history(self, session_id: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]

    def clear_history(self, session_id: str):
        self.sessions[session_id] = []

    def generate_summary(self, resume_text: str, provider: str) -> str:
        llm = LLMFactory.get_llm(provider)
        messages = [
            SystemMessage(content="You are an elite career advisor. Analyze this resume and provide a structured professional summary, highlighting strengths, weaknesses, and ATS-compatibility."),
            HumanMessage(content=f"Resume:\n{resume_text}")
        ]
        response = llm.invoke(messages)
        return response.content
    
    def generate_summary(self, resume_text: str, provider: str) -> dict:
        """Now returns a dictionary containing the text summary, ATS score, and chart."""
        llm = LLMFactory.get_llm(provider)
        analytics = AnalyticsService()
        
        messages = [
            SystemMessage(content="You are an elite career advisor. Analyze this resume and provide a structured professional summary, highlighting strengths and weaknesses."),
            HumanMessage(content=f"Resume:\n{resume_text}")
        ]
        
        # 1. Get LLM Summary
        response = llm.invoke(messages)
        
        # 2. Get Data Science Analytics
        ats_score = analytics.calculate_ats_score(resume_text)
        chart_base64 = analytics.generate_skill_radar_chart(resume_text)
        
        return {
            "summary_text": response.content,
            "ats_score": ats_score,
            "chart_base64": chart_base64
        }

    def ask_question(self, session_id: str, resume_text: str, question: str, provider: str) -> str:
        llm = LLMFactory.get_llm(provider)
        history = self.get_history(session_id)

        # Build prompt using context and history
        messages = [
            SystemMessage(content=(
                "You are an elite career advisor. "
                "Base your advice entirely on the provided resume context. "
                "Be direct, actionable, and professional."
            )),
            HumanMessage(content=f"RESUME CONTEXT:\n{resume_text}")
        ]

        # Inject memory
        for entry in history:
            messages.append(HumanMessage(content=entry["user"]))
            messages.append(AIMessage(content=entry["ai"]))

        # Add new question
        messages.append(HumanMessage(content=question))

        # Get response
        response = llm.invoke(messages)
        
        # Save to memory (limit to last 5 exchanges to save tokens)
        history.append({"user": question, "ai": response.content})
        if len(history) > 5:
            history.pop(0)

        return response.content