from tools.rag.rag_tool import RAGTool
from tools.rag.specialized_tools import SpecializedRAGTools

class COOAgent:
    def __init__(self):
        self.rag_tool = RAGTool().get_tool()
        # Ou pour les tools spécialisés:
        self.specialized_rag = SpecializedRAGTools()
    
    @property
    def tools(self):
        return [
            self.rag_tool,
            self.specialized_rag.get_support_tool(),
            self.specialized_rag.get_technical_tool(), 
            self.specialized_rag.get_hr_tool()
        ]