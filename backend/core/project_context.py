class UnifiedProjectContext:

    def __init__(self):

        self.features = []

        self.tasks = []

        self.contributors = []

        self.documents = []

        self.timeline_events = []

        self.activity = []

        self.semantic_chunks = []

        self.risks = []

        self.ai_insights = []

    def to_dict(self):

        return {
            "features": self.features,
            "tasks": self.tasks,
            "contributors": self.contributors,
            "documents": self.documents,
            "timeline_events": self.timeline_events,
            "activity": self.activity,
            "semantic_chunks": self.semantic_chunks,
            "risks": self.risks,
            "ai_insights": self.ai_insights
        }