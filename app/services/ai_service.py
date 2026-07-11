class AIService:

    async def chat(
        self,
        message: str,
    ) -> str:

        return f"AI menerima: {message}"