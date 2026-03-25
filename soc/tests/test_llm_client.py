import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
import json

from engine.core.llm_client import LLMClient

class TestLLMClient(unittest.IsolatedAsyncioTestCase):
    
    @patch("engine.core.llm_client.AsyncOpenAI")
    async def test_generate_json(self, MockOpenAI):
        # Setup mock
        mock_client_instance = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"status": "success"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        
        client = LLMClient(api_key="test", base_url="http://test")
        
        # Test standard parsing
        result = await client.generate_json("Test prompt", "System inst")
        self.assertEqual(result, {"status": "success"})
        
        # Test markdown stripping
        mock_message.content = '```json\n{"status": "stripped"}\n```'
        result2 = await client.generate_json("Test prompt")
        self.assertEqual(result2, {"status": "stripped"})

    @patch("engine.core.llm_client.AsyncOpenAI")
    async def test_generate_chat_json(self, MockOpenAI):
        mock_client_instance = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"chat": "history"}'
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        
        client = LLMClient(api_key="test", base_url="http://test")
        messages = [{"role": "user", "content": "Hello"}]
        
        result_json, result_raw = await client.generate_chat_json(messages)
        self.assertEqual(result_json, {"chat": "history"})
        self.assertEqual(result_raw, '{"chat": "history"}')

    @patch("engine.core.llm_client.AsyncOpenAI")
    async def test_get_embedding(self, MockOpenAI):
        mock_client_instance = MockOpenAI.return_value
        mock_response = MagicMock()
        mock_data = MagicMock()
        mock_data.embedding = [0.1, 0.2, 0.3]
        mock_response.data = [mock_data]
        mock_client_instance.embeddings.create = AsyncMock(return_value=mock_response)
        
        client = LLMClient(api_key="test", base_url="http://test")
        result = await client.get_embedding("Test text")
        self.assertEqual(result, [0.1, 0.2, 0.3])

if __name__ == "__main__":
    unittest.main()
