"""
Summarization module for generating article summaries.
Supports both LLM-based and extractive summarization.
"""

from typing import List, Optional
from sources.arxiv_source import Article


class Summarizer:
    """Generates summaries for articles using LLM or extractive methods."""
    
    def __init__(self, openai_api_key: str = "", gemini_api_key: str = "", groq_api_key: str = "", max_summary_length: int = 400):
        """
        Initialize the summarizer with API keys.
        
        Args:
            openai_api_key: OpenAI API key.
            gemini_api_key: Gemini API key.
            groq_api_key: Groq API key.
            max_summary_length: Maximum length of generated summary.
        """
        self.max_summary_length = max_summary_length
        self._openai_client = None
        self._gemini_model = None
        self._groq_client = None
        
        # Initialize Groq (OpenAI-compatible)
        if groq_api_key:
            try:
                from openai import OpenAI
                self._groq_client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=groq_api_key
                )
            except ImportError:
                print("OpenAI library not installed (needed for Groq)")

        # Initialize OpenAI
        if openai_api_key and not self._groq_client:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=openai_api_key)
                if not openai_api_key.startswith('sk-'):
                    self._openai_client = None
            except ImportError:
                print("OpenAI library not installed")
        
        # Initialize Gemini
        if gemini_api_key and not self._openai_client and not self._groq_client:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_api_key)
                self._gemini_model = genai.GenerativeModel('gemini-flash-lite-latest')
            except ImportError:
                print("Google Generative AI library not installed")
    
    @property
    def has_llm(self) -> bool:
        """Check if an LLM is available for summarization."""
        return self._openai_client is not None or self._gemini_model is not None or self._groq_client is not None
    
    def summarize(self, article: Article) -> str:
        """
        Generate a summary for an article.
        
        Falls back to extractive summarization if no LLM is available.
        
        Args:
            article: Article object with title and summary/abstract.
            
        Returns:
            Generated summary string.
        """
        # Try LLM summarization
        if self.has_llm:
            try:
                import time
                time.sleep(0.5) # Reduced sleep for better providers
                return self._summarize_with_llm(article)
            except Exception as e:
                print(f"LLM summarization failed: {e}")
        
        # Fallback to extractive
        return self._extractive_summary(article.summary or article.title)
    
    def summarize_batch(self, articles: List[Article], max_batch: int = 15) -> List[Article]:
        """
        Summarize a batch of articles.
        
        Args:
            articles: List of Article objects.
            max_batch: Maximum number to process.
            
        Returns:
            Articles with updated summaries.
        """
        for article in articles[:max_batch]:
            article.summary = self.summarize(article)
        return articles
    
    def _summarize_with_llm(self, article: Article) -> str:
        """Use LLM to generate a structured summary."""
        prompt = f"""Summarize this content as a high-signal brief for a busy AI professional.
Focus on the 'why it matters' and 'key takeaways'.
Use 1-2 bullet points if there are multiple important facts.
Keep it under {self.max_summary_length} characters.

Title: {article.title}
Source: {article.source}
Content: {article.summary[:1500]}

Summary:"""
        
        if self._groq_client:
            response = self._groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()[:self.max_summary_length]

        if self._openai_client:
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()[:self.max_summary_length]
        
        elif self._gemini_model:
            response = self._gemini_model.generate_content(prompt)
            return response.text.strip()[:self.max_summary_length]
        
        return article.summary[:self.max_summary_length]
    
    def _extractive_summary(self, text: str) -> str:
        """
        Simple extractive summarization.
        
        Takes the first few sentences that fit within the limit.
        """
        if not text:
            return ""
        
        # Split into sentences
        sentences = text.replace('\n', ' ').split('. ')
        
        summary = []
        total_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Add period if missing
            if not sentence.endswith('.'):
                sentence += '.'
            
            if total_length + len(sentence) + 1 <= self.max_summary_length:
                summary.append(sentence)
                total_length += len(sentence) + 1
            else:
                break
        
        result = ' '.join(summary)
        
        # If we couldn't fit any sentences, just truncate
        if not result and text:
            result = text[:self.max_summary_length - 3] + '...'
        
        return result


# Quick test
if __name__ == '__main__':
    summarizer = Summarizer()
    
    test_article = Article(
        title="New Breakthrough in Large Language Models",
        url="https://example.com",
        source="Test",
        published=None,
        summary="Researchers have developed a new architecture for large language models that significantly improves both efficiency and performance. The new approach uses a novel attention mechanism that reduces computational requirements by 50% while maintaining state-of-the-art results on standard benchmarks. This breakthrough could lead to more accessible AI systems that require less hardware resources."
    )
    
    print("Original summary:")
    print(test_article.summary)
    print(f"\nLength: {len(test_article.summary)}")
    
    summary = summarizer.summarize(test_article)
    print(f"\nGenerated summary:")
    print(summary)
    print(f"Length: {len(summary)}")
