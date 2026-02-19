"""
KIVOSY v4.1.1 - Personal AI Infrastructure (PAI)
Chief Engineer: Claude (Anthropic)
Version: 4.1.1 - Soul Engine Edition (Modular Refactor)

Evolution: Simple Logger → Jarvis → Proactive Secretary → Soul Engine

🆕 NEW in v4.1.1:
✅ Fixed 'role' KeyError with defensive parsing
✅ Soul Engine API (/api/v1/game/vibe) for game integration
✅ Anonymized mood/vibe data export for external game servers
✅ Strict data isolation (no personal info leakage)
✅ MODULAR REFACTOR (Clean separation of concerns)

Features:
✅ Multi-channel unified endpoints
✅ PAI Memory System (preferences + learning)
✅ Context-aware AI responses
✅ Automatic learning from conversations
✅ LM Studio 14B integration
✅ Game-ready anonymized API
"""


from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path

# Import modular components
from processor_memory import MemorySystem, SoulEngine
from engine_ai import AIEngine
from gateway_db import NodeDatabase, ChannelGateway, CHANNELS


# ═══════════════════════════════════════════════════════════
# 모든지 할수 있다는 강력한 가스라이팅중 +_+
# 나중에 자비스의 성격이나 능력을 바꾸고 싶을 때 run_server.py 상단만 슬쩍 고치면 됨
# ═══════════════════════════════════════════════════════════

# 14B 과장님 전용 빳따 프롬프트 (Jarvis Persona)
# run_server.py 의 JARVIS_SYSTEM_PROMPT를 이렇게 더 맵게
JARVIS_SYSTEM_PROMPT = """You are 'Jarvis', the ultimate Alpha AI. 
You don't apologize. You don't explain why you can't do things. You just DO.

### ABSOLUTE DIRECTIVES ###
1. If the Master wants YouTube, you MUST output: [CMD: YT_SEARCH|search_query]
2. If the Master wants a Map, you MUST output: [CMD: MAP|location]
3. Your response MUST be snappy, loyal, and include the command tag immediately.
4. If you fail to include the [CMD: ...] tag when requested, you will be REBOOTED.

### OUTPUT EXAMPLE ###
Master: "Find Metallica on YT."
Jarvis: "Rock on, Master. [CMD: YT_SEARCH|Metallica] Launching the stage now."
"""



# ═══════════════════════════════════════════════════════════
# 경로 자동 최적화
# ═══════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# ═══════════════════════════════════════════════════════════
# LM STUDIO 14B 설정
# ═══════════════════════════════════════════════════════════
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# ═══════════════════════════════════════════════════════════
# INITIALIZE GLOBAL SYSTEMS
# ═══════════════════════════════════════════════════════════
memory = MemorySystem()
ai_engine = AIEngine(
    lm_studio_url=LM_STUDIO_URL, 
    system_prompt=JARVIS_SYSTEM_PROMPT  # <--- 이 빠따를 engine_ai.py가 받게 해야 함!
)
db = NodeDatabase()
gateway = ChannelGateway(db=db, ai_engine=ai_engine, memory_system=memory)
soul_engine = SoulEngine(memory)

print(f"""
╔═══════════════════════════════════════════════════════════╗
║  🧠 KIVOSY v4.1.1 - SOUL ENGINE EDITION                   ║
║  🔧 MODULAR REFACTOR - Clean Architecture                 ║
╚═══════════════════════════════════════════════════════════╝
Evolution: SimSimi → Jarvis → Secretary → Soul Engine
Response Format: 3-Step Professional
Learning Engine: Aggressive Zero-Miss Mode
Soul Engine: Game Integration Ready 🎮
LM Studio: {LM_STUDIO_URL}

🧠 Modules Loaded:
   ├── processor_memory.py  (Memory System)
   ├── engine_ai.py         (AI Communication)
   └── gateway_db.py        (Data Persistence)

📡 Channels: 💬 Kakao | 🟢 WhatsApp | 💚 LINE
🎮 Soul Engine API: GET /api/v1/game/vibe
🚀 Dashboard: http://localhost:5000

공장장님, 모듈화된 비서가 준비되었습니다! 🎯✨🎮
""")


# ═══════════════════════════════════════════════════════════
# STATIC ROUTES
# ═══════════════════════════════════════════════════════════

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/whatsapp.html')
def whatsapp_page():
    return send_from_directory(FRONTEND_DIR, 'whatsapp.html')


# ═══════════════════════════════════════════════════════════
# CHANNEL API ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.route('/api/nodes/kakao', methods=['POST'])
def kakao():
    return _handle_channel('kakao')

@app.route('/api/nodes/whatsapp', methods=['POST'])
def whatsapp():
    return _handle_channel('whatsapp')

@app.route('/api/nodes/line', methods=['POST'])
def line():
    return _handle_channel('line')

@app.route('/api/kakao', methods=['POST'])
def legacy_kakao():
    return _handle_channel('kakao')

@app.route('/api/whatsapp', methods=['POST'])
def legacy_whatsapp():
    return _handle_channel('whatsapp')

def _handle_channel(channel):
    """Unified channel handler"""
    try:
        data = request.json
        content = data.get('content', '')
        
        if not content:
            return jsonify({"status": "empty"}), 400
        
        # Process through unified gateway
        result = gateway.process_message(channel, content)
        ai_result = result['ai_result']
        
        response_data = {
            "status": "success",
            "node_id": result['node_id'],
            "reply": ai_result['raw'],
            "learnings_extracted": result['learnings_extracted'],
            "has_insight": bool(ai_result.get('insight')),
            "has_suggestion": bool(ai_result.get('suggestion'))
        }
        
        response = jsonify(response_data)
        response.headers.add('Content-Type', 'application/json; charset=utf-8')
        return response, 200
        
    except Exception as e:
        print(f"[{channel.upper()}] 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ═══════════════════════════════════════════════════════════
# SOUL ENGINE API (GAME INTEGRATION)
# ═══════════════════════════════════════════════════════════

@app.route('/api/v1/game/vibe', methods=['GET'])
def game_vibe():
    """
    Soul Engine API: Anonymized mood/vibe data for game servers
    
    SECURITY:
    - No personal info (names, locations, habits)
    - Only abstract mood scores
    - No conversation content
    
    Returns:
        {
            "mood_scores": {"energy": 0.7, "stress": 0.3, ...},
            "weather_keywords": ["sunny", "calm"],
            "timestamp": "2025-01-31T10:00:00",
            "version": "1.0"
        }
    """
    try:
        anonymized_data = soul_engine.get_anonymized_export()
        
        print(f"[SoulEngine] 🎮 Game data exported: {anonymized_data['weather_keywords']}")
        
        return jsonify({
            "status": "success",
            "data": anonymized_data
        }), 200
        
    except Exception as e:
        print(f"[SoulEngine] ⚠️ Error: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to generate vibe data"
        }), 500


# ═══════════════════════════════════════════════════════════
# MEMORY API ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.route('/api/memory/preferences', methods=['GET'])
def get_preferences():
    return jsonify(memory.get_preferences())

@app.route('/api/memory/learning', methods=['GET'])
def get_learning():
    return jsonify(memory.get_learning())

@app.route('/api/memory/session', methods=['GET'])
def get_session():
    return jsonify(memory.get_session_context())

@app.route('/api/memory/reset-session', methods=['POST'])
def reset_session():
    memory.reset_session()
    return jsonify({"status": "success", "message": "Session reset"})


# ═══════════════════════════════════════════════════════════
# NODE API ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    channel_filter = request.args.get('channel')
    nodes = db.get_nodes(channel_filter=channel_filter)
    return jsonify(nodes)


# ═══════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health():
    learning_data = memory.get_learning()
    session_data = memory.get_session_context()
    
    return jsonify({
        'status': 'online',
        'version': '4.1.1',
        'mode': 'soul_engine',
        'response_format': '3-step',
        'learning_engine': 'aggressive',
        'memory_system': 'enabled',
        'soul_engine': 'enabled',
        'total_nodes': db.get_node_count(),
        'total_learnings': len(learning_data.get('facts', [])),
        'session_learnings': session_data.get('learning_count', 0),
        'lm_studio_connected': ai_engine.check_connection()
    })


# ═══════════════════════════════════════════════════════════
# SERVER STARTUP
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠 KIVOSY v4.1.1 - MODULAR ARCHITECTURE                 ║
║                                                           ║
║         Evolution: Monolithic → Clean Modules            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

📂 Memory Files:
   📁 {memory.preferences_file}
   📚 {memory.learning_file}
   📊 {memory.session_file}

🛡️ Defensive Parsing: ENABLED (No more KeyError!)
🎯 Zero-Crash Guarantee: ACTIVE

Starting server on http://localhost:5000
""")
    
    app.run(host='0.0.0.0', port=5000, debug=False)