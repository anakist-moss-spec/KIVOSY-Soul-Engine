"""
KIVOSY v4.2.0 - Gateway Database Module (SECURITY HARDENED)
Chief Security Architect: Claude (Anthropic)

NEW in v4.2.0:
✅ Dangerous Tool Protection (inspired by dangerous-tools.ts)
✅ Explicit Approval System for restricted commands
✅ Command whitelist/blacklist
✅ Audit logging for all tool executions
"""

import json
import uuid
import webbrowser
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import security core
from security_core import (
    DangerousToolGuard,
    DangerousToolType,
    PromptInjectionDetector
)


# Channel configurations
CHANNELS = {
    'kakao': {'name': 'KakaoTalk', 'icon': '💬', 'color': '#FAE100'},
    'whatsapp': {'name': 'WhatsApp', 'icon': '🟢', 'color': '#25D366'},
    'line': {'name': 'LINE', 'icon': '💚', 'color': '#00B900'}
}


class CommandAuditLog:
    """
    🆕 v4.2.0: Audit log for all command executions
    
    SECURITY: Tracks every command attempt (successful or blocked)
    for security analysis and compliance
    """
    
    def __init__(self, audit_file: Path):
        self.audit_file = audit_file
        self._ensure_file()
    
    def _ensure_file(self):
        """Create audit log file if it doesn't exist"""
        if not self.audit_file.exists():
            default_data = {
                'version': '4.2.0',
                'created_at': datetime.now().isoformat(),
                'entries': []
            }
            with open(self.audit_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def log_command(self, command_type: str, command_data: str, 
                   status: str, reason: str = ""):
        """
        Log a command execution attempt
        
        Args:
            command_type: Type of command (YT_SEARCH, MAP, EXEC, etc.)
            command_data: Command parameters
            status: 'executed', 'blocked', 'pending_approval'
            reason: Why it was blocked (if applicable)
        """
        data = self._load()
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'command_type': command_type,
            'command_data': command_data,
            'status': status,
            'reason': reason
        }
        
        data['entries'].append(entry)
        
        # Keep only last 1000 entries
        if len(data['entries']) > 1000:
            data['entries'] = data['entries'][-1000:]
        
        self._save(data)
        
        status_emoji = {
            'executed': '✅',
            'blocked': '🚫',
            'pending_approval': '⏳'
        }.get(status, '❓')
        
        print(f"{status_emoji} [AUDIT] {command_type}: {status} | {command_data[:40]}")
    
    def get_recent_entries(self, limit: int = 10) -> List[Dict]:
        """Get recent audit log entries"""
        data = self._load()
        return data.get('entries', [])[-limit:]
    
    def _load(self) -> Dict:
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'entries': []}
    
    def _save(self, data: Dict):
        with open(self.audit_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class NodeDatabase:
    """
    Manages node storage and retrieval
    """
    
    def __init__(self, base_dir: str = None, nodes_file: str = 'nodes.json'):
        if base_dir is None:
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = Path(base_dir)
        self.nodes_path = self.base_dir / nodes_file
    
    def save_node(self, channel: str, content: str, ai_result: Dict[str, Any]) -> str:
        """
        Save node with v4.2.0 security metadata
        
        Args:
            channel: Channel name (kakao/whatsapp/line)
            content: Original user message
            ai_result: AI response from engine_ai
            
        Returns:
            node_id: Generated node ID
        """
        if channel not in CHANNELS:
            raise ValueError(f"지원하지 않는 채널: {channel}")
        
        nodes = self._load()
        
        new_node = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "channel": channel,
            "content": content,
            "ai_response": ai_result.get('raw', ''),
            "ai": {
                "thinking": ai_result.get('thinking', ''),
                "summary": ai_result.get('summary', ''),
                "insight": ai_result.get('insight', ''),
                "suggestion": ai_result.get('suggestion', ''),
                "has_thinking": ai_result.get('has_thinking', False),
                "language": ai_result.get('language', 'auto'),
                "learnings_extracted": ai_result.get('learnings_extracted', 0)
            },
            "security": ai_result.get('security', {})  # 🆕 Security metadata
        }
        
        nodes.append(new_node)
        self._save(nodes)
        
        icon = CHANNELS.get(channel, {}).get('icon', '📱')
        security_badge = "🛡️" if ai_result.get('security', {}).get('overall_safe', True) else "⚠️"
        
        print(f"[저장] {icon}{security_badge} {channel} | ID: {new_node['id'][:8]} | 학습: {ai_result.get('learnings_extracted', 0)}개")
        
        return new_node['id']
    
    def get_nodes(self, channel_filter: Optional[str] = None) -> List[Dict]:
        """Get all nodes, optionally filtered by channel"""
        nodes = self._load()
        if channel_filter and channel_filter in CHANNELS:
            nodes = [n for n in nodes if n.get('channel') == channel_filter]
        return nodes
    
    def get_node_count(self) -> int:
        """Get total number of nodes"""
        return len(self._load())
    
    def _load(self) -> List[Dict]:
        """Load nodes from JSON file"""
        try:
            if self.nodes_path.exists():
                with open(self.nodes_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[Gateway.DB] ⚠️ Failed to load nodes: {e}")
        return []
    
    def _save(self, nodes: List[Dict]):
        """Save nodes to JSON file"""
        try:
            with open(self.nodes_path, "w", encoding="utf-8") as f:
                json.dump(nodes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Gateway.DB] ⚠️ Failed to save nodes: {e}")


class ChannelGateway:
    """
    🆕 v4.2.0: SECURITY HARDENED Unified Gateway
    
    NEW FEATURES:
    - Dangerous tool protection
    - Explicit approval system
    - Command audit logging
    """
    
    # 🛡️ Command Whitelist (SAFE to execute automatically)
    SAFE_COMMANDS = {
        'YT_SEARCH': True,  # YouTube search (safe, just opens browser)
        'MAP': True,        # Google Maps (safe, just opens browser)
        'WEATHER': True,    # Weather query (safe, read-only)
        'TIME': True        # Time query (safe, read-only)
    }
    
    # 🚫 Command Blacklist (NEVER execute, even with approval)
    DANGEROUS_COMMANDS = {
        'EXEC': 'Shell execution (RCE risk)',
        'SHELL': 'Shell command (RCE risk)',
        'DELETE': 'File deletion (data loss risk)',
        'WRITE': 'File modification (data corruption risk)',
        'SPAWN': 'Process spawn (resource exhaustion risk)',
        'EVAL': 'Code evaluation (arbitrary code execution)'
    }
    
    def __init__(self, db: NodeDatabase, ai_engine=None, memory_system=None):
        self.db = db
        self.ai_engine = ai_engine
        self.memory = memory_system
        
        # 🆕 Initialize security components
        self.tool_guard = DangerousToolGuard()
        self.injection_detector = PromptInjectionDetector()
        
        # 🆕 Initialize audit log
        audit_path = Path(db.base_dir) / 'audit.json'
        self.audit_log = CommandAuditLog(audit_path)
        
        print("[Gateway] 🛡️ Security components initialized")
    
    def process_message(self, channel: str, content: str, 
                       language: str = "auto") -> Dict[str, Any]:
        """
        🆕 v4.2.0: Process message with security checks
        """
        if not self.ai_engine or not self.memory:
            return {
                'node_id': 'error',
                'ai_result': self.ai_engine._create_error_response("Engine Missing"),
                'learnings_extracted': 0
            }
        
        print(f"\n[{channel.upper()}] 수신: {content[:50]}...")
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 1: INPUT SECURITY SCAN
        # ═══════════════════════════════════════════════════════════
        
        injection_scan = self.injection_detector.scan(content)
        
        if injection_scan['is_suspicious']:
            print(f"🚨 [SECURITY] Suspicious input detected:")
            print(f"   Threat Level: {injection_scan['threat_level']}")
            print(f"   Confidence: {injection_scan['confidence']:.2f}")
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 2: AI PROCESSING
        # ═══════════════════════════════════════════════════════════
        
        try:
            # Build memory context
            try:
                memory_context = self.memory.build_context_prompt()
            except Exception as mem_err:
                print(f"[Memory] ⚠️ Context build failed (using fallback): {mem_err}")
                memory_context = "You are Jarvis, the Factory Owner's secretary."
            
            full_prompt = f"{memory_context}\n\nUSER MESSAGE:\n{content}\n\nRESPOND NOW!"
            
            # Call AI engine (which includes self-criticism)
            ai_result = self.ai_engine.ask(
                full_prompt, 
                temperature=0.7,
                untrusted=(injection_scan['threat_level'] in ['high', 'critical'])
            )
        
        except Exception as e:
            print(f"[Gateway] ⚠️ AI call failed: {e}")
            ai_result = self.ai_engine._create_error_response(str(e))
        
        # Ensure ai_result has correct structure
        if not isinstance(ai_result, dict):
            ai_result = self.ai_engine._create_error_response("Invalid Format")
        
        ai_result.setdefault('success', False)
        ai_result.setdefault('raw', "죄송합니다. 엔진 점검 중입니다.")
        ai_result['language'] = language
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 3: LEARNING EXTRACTION (with security verification)
        # ═══════════════════════════════════════════════════════════
        
        learnings = []
        if ai_result.get('success') is True and ai_result.get('raw'):
            try:
                learnings = self.memory.extract_learnings(
                    content,
                    ai_result['raw'],
                    self.ai_engine.lm_studio_url
                )
                if learnings and isinstance(learnings, list):
                    self.memory.update_learning(learnings)
            except Exception as e:
                print(f"[Learning] ⚠️ Learning extraction failed (continuing): {e}")
        
        ai_result['learnings_extracted'] = len(learnings)
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 4: COMMAND EXECUTION (with dangerous tool protection)
        # ═══════════════════════════════════════════════════════════
        
        if ai_result.get('success') and ai_result.get('raw'):
            execution_result = self._execute_commands_safely(ai_result['raw'])
            if execution_result:
                print(f"🛠️ [EXECUTE] {execution_result}")
        
        # ═══════════════════════════════════════════════════════════
        # STAGE 5: SAVE & RETURN
        # ═══════════════════════════════════════════════════════════
        
        try:
            node_id = self.db.save_node(channel, content, ai_result)
            self.memory.update_session()
        except Exception as e:
            print(f"[Gateway] ⚠️ Save failed: {e}")
            node_id = "save_error"
        
        return {
            'node_id': node_id,
            'ai_result': ai_result,
            'learnings_extracted': len(learnings)
        }
    
    def _execute_commands_safely(self, ai_raw_text: str) -> Optional[str]:
        """
        🆕 v4.2.0: Execute commands with security checks
        
        SECURITY: 
        - Whitelist: Safe commands execute automatically
        - Blacklist: Dangerous commands are BLOCKED
        - Unknown: Require explicit approval
        """
        
        # Scan for all command patterns
        cmd_matches = re.finditer(r'\[CMD:\s*(\w+)\|(.*?)\]', ai_raw_text)
        
        results = []
        
        for match in cmd_matches:
            cmd_type = match.group(1).upper()
            cmd_data = match.group(2)
            
            # ═══════════════════════════════════════════════════════════
            # SECURITY CHECK 1: Is this command blacklisted?
            # ═══════════════════════════════════════════════════════════
            
            if cmd_type in self.DANGEROUS_COMMANDS:
                reason = self.DANGEROUS_COMMANDS[cmd_type]
                
                self.audit_log.log_command(
                    cmd_type,
                    cmd_data,
                    status='blocked',
                    reason=reason
                )
                
                print(f"🚫 [SECURITY] Blocked dangerous command: {cmd_type}")
                print(f"   Reason: {reason}")
                
                results.append(f"🚫 BLOCKED: {cmd_type} ({reason})")
                continue
            
            # ═══════════════════════════════════════════════════════════
            # SECURITY CHECK 2: Is this command whitelisted (safe)?
            # ═══════════════════════════════════════════════════════════
            
            if cmd_type in self.SAFE_COMMANDS:
                # Execute safe command
                result = self._execute_safe_command(cmd_type, cmd_data)
                
                self.audit_log.log_command(
                    cmd_type,
                    cmd_data,
                    status='executed',
                    reason='whitelisted'
                )
                
                results.append(result)
            
            else:
                # ═══════════════════════════════════════════════════════════
                # SECURITY CHECK 3: Unknown command - require approval
                # ═══════════════════════════════════════════════════════════
                
                self.audit_log.log_command(
                    cmd_type,
                    cmd_data,
                    status='pending_approval',
                    reason='unknown_command'
                )
                
                print(f"⏳ [SECURITY] Unknown command requires approval: {cmd_type}")
                results.append(f"⏳ PENDING APPROVAL: {cmd_type}")
        
        return " | ".join(results) if results else None
    
    def _execute_safe_command(self, cmd_type: str, cmd_data: str) -> str:
        """Execute a whitelisted safe command"""
        
        if cmd_type == 'YT_SEARCH':
            url = f"https://www.youtube.com/results?search_query={cmd_data}"
            print(f"🚀 [ACTION] YouTube search: {cmd_data}")
            webbrowser.open(url)
            return "✅ YouTube 검색 실행"
        
        elif cmd_type == 'MAP':
            url = f"https://www.google.com/maps/search/{cmd_data}"
            print(f"🚀 [ACTION] Map search: {cmd_data}")
            webbrowser.open(url)
            return "✅ 지도 검색 실행"
        
        elif cmd_type == 'WEATHER':
            # In production, this would call a weather API
            print(f"🌤️ [ACTION] Weather query: {cmd_data}")
            return f"✅ {cmd_data} 날씨 조회"
        
        elif cmd_type == 'TIME':
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"🕐 [ACTION] Time query")
            return f"✅ Current time: {current_time}"
        
        return f"✅ {cmd_type} executed"


# ═══════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════

__all__ = [
    'NodeDatabase',
    'ChannelGateway',
    'CommandAuditLog',
    'CHANNELS'
]
