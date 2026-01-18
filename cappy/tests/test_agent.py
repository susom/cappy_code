"""Integration tests for cappy.agent module."""

import pytest
import json
from cappy.agent import (
    get_system_prompt,
    parse_agent_response,
    AGENT_RESPONSE_SCHEMA,
)


class TestSystemPrompt:
    """Tests for system prompt generation."""
    
    @pytest.mark.unit
    def test_system_prompt_structure(self):
        """Test system prompt has required sections."""
        prompt = get_system_prompt()
        
        assert "You are Cappy" in prompt
        assert "Available tools:" in prompt
        assert "scan" in prompt
        assert "search" in prompt
        assert "read" in prompt
        assert "write" in prompt
        assert "edit" in prompt
        assert "delete" in prompt
        assert "move" in prompt
        assert "copy" in prompt
    
    @pytest.mark.unit
    def test_system_prompt_json_schema(self):
        """Test system prompt includes JSON schema."""
        prompt = get_system_prompt()
        
        assert "AGENT_RESPONSE_SCHEMA" in prompt or "JSON" in prompt
        assert "action" in prompt
        assert "tool_call" in prompt


class TestResponseParsing:
    """Tests for agent response parsing."""
    
    @pytest.mark.unit
    def test_parse_done_response(self):
        """Test parsing done response."""
        response = json.dumps({
            "action": "done",
            "message": "Task completed successfully"
        })
        
        result = parse_agent_response(response)
        
        assert result["action"] == "done"
        assert result["message"] == "Task completed successfully"
    
    @pytest.mark.unit
    def test_parse_tool_call_response(self):
        """Test parsing tool call response."""
        response = json.dumps({
            "action": "tool_call",
            "tool_name": "read",
            "tool_input": {"path": "test.py"},
            "reasoning": "Need to read the file"
        })
        
        result = parse_agent_response(response)
        
        assert result["action"] == "tool_call"
        assert result["tool_name"] == "read"
        assert result["tool_input"]["path"] == "test.py"
        assert result["reasoning"] == "Need to read the file"
    
    @pytest.mark.unit
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        response = "This is not JSON"
        
        result = parse_agent_response(response)
        
        assert result is None
    
    @pytest.mark.unit
    def test_parse_missing_action(self):
        """Test parsing response without action field."""
        response = json.dumps({
            "message": "No action field"
        })
        
        result = parse_agent_response(response)
        
        assert result is None


class TestAgentResponseSchema:
    """Tests for agent response schema."""
    
    @pytest.mark.unit
    def test_schema_structure(self):
        """Test schema has required structure."""
        schema = AGENT_RESPONSE_SCHEMA
        
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "action" in schema["properties"]
        assert "required" in schema
        assert "action" in schema["required"]
    
    @pytest.mark.unit
    def test_schema_actions(self):
        """Test schema defines valid actions."""
        schema = AGENT_RESPONSE_SCHEMA
        action_enum = schema["properties"]["action"]["enum"]
        
        assert "tool_call" in action_enum
        assert "done" in action_enum
    
    @pytest.mark.unit
    def test_schema_tools(self):
        """Test schema defines all tools."""
        schema = AGENT_RESPONSE_SCHEMA
        
        # Find tool_name enum
        tool_name_enum = None
        if "properties" in schema and "tool_name" in schema["properties"]:
            tool_name_enum = schema["properties"]["tool_name"].get("enum", [])
        
        if tool_name_enum:
            assert "scan" in tool_name_enum
            assert "search" in tool_name_enum
            assert "read" in tool_name_enum
            assert "write" in tool_name_enum
            assert "edit" in tool_name_enum
            assert "delete" in tool_name_enum
            assert "move" in tool_name_enum
            assert "copy" in tool_name_enum
