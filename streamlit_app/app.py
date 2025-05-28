import streamlit as st
import requests
from typing import List, Dict
import io

# Page config
st.set_page_config(
    page_title="Multi-Agent Finance Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .agent-status {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 0.5rem 0;
    }
    
    .agent-healthy {
        background-color: #d4edda;
        border-color: #c3e6cb;
    }
    
    .agent-unhealthy {
        background-color: #f8d7da;
        border-color: #f5c6cb;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration URLs
ORCHESTRATOR_URL = "http://localhost:8000"

AGENT_URLS = {
    "api": "http://localhost:8001",
    "scraping": "http://localhost:8002",
    "retriever": "http://localhost:8003",
    "analysis": "http://localhost:8004",
    "language": "http://localhost:8005",
    "voice": "http://localhost:8006"
}

def check_agent_health():
    """Check and display agent health status with detailed information"""
    for agent_name, url in AGENT_URLS.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                st.markdown(f'<div class="agent-status agent-healthy">✅ {agent_name.title()} Agent - {url}</div>', 
                          unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="agent-status agent-unhealthy">❌ {agent_name.title()} Agent - HTTP {response.status_code} - {url}</div>', 
                          unsafe_allow_html=True)
        except requests.exceptions.ConnectionError:
            st.markdown(f'<div class="agent-status agent-unhealthy">❌ {agent_name.title()} Agent - Connection Failed - {url}</div>', 
                      unsafe_allow_html=True)
        except requests.exceptions.Timeout:
            st.markdown(f'<div class="agent-status agent-unhealthy">❌ {agent_name.title()} Agent - Timeout - {url}</div>', 
                      unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="agent-status agent-unhealthy">❌ {agent_name.title()} Agent - Error: {str(e)[:50]} - {url}</div>', 
                      unsafe_allow_html=True)

def process_query(query: str, symbols: List[str], include_analysis: bool, response_type: str) -> Dict:
    """Process user query through the orchestrator"""
    try:
        response = requests.post(
            f"{ORCHESTRATOR_URL}/process",
            json={
                "query": query,
                "symbols": symbols,
                "include_analysis": include_analysis,
                "response_type": response_type
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_resp = data.get("ai_response", {})

            return {
                "content": ai_resp.get("response", "No response generated"),
                "confidence": ai_resp.get("confidence", 0.0),
                "processing_time": ai_resp.get("processing_time", None),
                "sources": ai_resp.get("sources", [])
            }
        else:
            return {
                "content": f"Error: Service returned status {response.status_code}",
                "confidence": 0.0,
                "processing_time": 0.0,
                "sources": []
            }
    except Exception as e:
        return {
            "content": f"Error processing request: {str(e)}",
            "confidence": 0.0,
            "processing_time": 0.0,
            "sources": []
        }

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "last_transcription" not in st.session_state:
        st.session_state.last_transcription = ""
    
    if "audio_processing_status" not in st.session_state:
        st.session_state.audio_processing_status = "idle"

def transcribe_audio_file(uploaded_file):
    """Transcribe uploaded audio file with enhanced error handling"""
    try:
        # Check if voice agent is available first
        try:
            health_check = requests.get(f"{AGENT_URLS['voice']}/health", timeout=5)
            if health_check.status_code != 200:
                return {
                    "success": False,
                    "error": f"Voice agent is not healthy (status: {health_check.status_code}). Please check if the voice service is running on port 8006.",
                    "text": ""
                }
        except requests.exceptions.RequestException:
            return {
                "success": False,
                "error": "Cannot connect to voice agent. Please ensure the voice service is running on http://localhost:8006",
                "text": ""
            }
        
        # Validate file size and type
        file_size = len(uploaded_file.getvalue())
        max_size = 50 * 1024 * 1024  # 50MB limit
        
        if file_size > max_size:
            return {
                "success": False,
                "error": f"File too large ({file_size / (1024*1024):.1f}MB). Maximum size is 50MB.",
                "text": ""
            }
        
        if file_size == 0:
            return {
                "success": False,
                "error": "File appears to be empty.",
                "text": ""
            }
        
        # Prepare file for upload
        files = {
            "file": (
                uploaded_file.name, 
                uploaded_file.getvalue(), 
                uploaded_file.type or "audio/wav"
            )
        }
        
        # Send to voice agent for transcription with detailed error handling
        response = requests.post(
            f"{AGENT_URLS['voice']}/transcribe", 
            files=files, 
            timeout=120
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                return {
                    "success": True,
                    "text": result.get("text", ""),
                    "confidence": result.get("confidence", 0.0)
                }
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON response from transcription service: {str(e)}",
                    "text": ""
                }
        else:
            # Try to get error details from response
            try:
                error_detail = response.json() if response.content else {}
                error_msg = error_detail.get("detail", f"HTTP {response.status_code}")
            except:
                error_msg = f"HTTP {response.status_code}"
            
            return {
                "success": False,
                "error": f"Transcription service error: {error_msg}. Check voice agent logs for details.",
                "text": ""
            }
            
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Transcription request timed out (120s). The audio file may be too long or the service is overloaded.",
            "text": ""
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Cannot connect to voice agent. Please verify that the voice service is running on http://localhost:8006",
            "text": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error during transcription: {str(e)}",
            "text": ""
        }

def synthesize_speech(text: str, voice: str = "alloy"):
    """Synthesize speech from text"""
    try:
        response = requests.post(
            f"{AGENT_URLS['voice']}/synthesize",
            json={"text": text, "voice": voice},
            timeout=60
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "audio_data": response.content
            }
        else:
            return {
                "success": False,
                "error": f"Speech synthesis failed with status {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error during speech synthesis: {str(e)}"
        }

def voice_interface():
    """Voice interface for the application"""
    st.subheader("🎤 Voice Input Interface")
    
    # Initialize session state
    initialize_session_state()
    
    # Audio file upload section
    st.markdown("### 📁 Audio File Upload")
    st.info("Upload an audio file (WAV, MP3, M4A) to transcribe and process")
    
    # Add voice service status check
    with st.expander("🔧 Voice Service Diagnostics"):
        st.markdown("**Voice Agent Status Check:**")
        try:
            voice_health = requests.get(f"{AGENT_URLS['voice']}/health", timeout=3)
            if voice_health.status_code == 200:
                st.success(f"✅ Voice agent is healthy at {AGENT_URLS['voice']}")
            else:
                st.error(f"❌ Voice agent returned status {voice_health.status_code}")
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot connect to voice agent at {AGENT_URLS['voice']}")
            st.markdown("**Troubleshooting steps:**")
            st.markdown("1. Check if the voice agent is running on port 8006")
            st.markdown("2. Verify the service started without errors")
            st.markdown("3. Check firewall/port blocking")
        except Exception as e:
            st.error(f"❌ Voice agent error: {str(e)}")
    
    uploaded_file = st.file_uploader(
        "Choose an audio file", 
        type=['wav', 'mp3', 'm4a', 'mp4', 'mpeg', 'mpga', 'webm'],
        help="Supported formats: WAV, MP3, M4A, MP4, MPEG, MPGA, WebM"
    )
    
    if uploaded_file is not None:
        # Display file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.success(f"✅ File uploaded: {uploaded_file.name} ({file_size_mb:.2f} MB)")
        
        # Check file size (warn if too large)
        if file_size_mb > 25:
            st.warning("⚠️ Large file detected. Processing may take longer.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Process Audio File", type="primary"):
                st.session_state.audio_processing_status = "processing"
                
                with st.spinner("Transcribing audio... This may take a moment."):
                    result = transcribe_audio_file(uploaded_file)
                    
                    if result["success"]:
                        st.success(f"📝 **Transcription successful!**")
                        st.text_area(
                            "Transcribed Text:", 
                            value=result["text"], 
                            height=100, 
                            key="transcription_display"
                        )
                        
                        # Store transcription in session state
                        st.session_state.last_transcription = result["text"]
                        st.session_state.audio_processing_status = "completed"
                        
                        if result.get("confidence", 0) > 0:
                            st.caption(f"🎯 Confidence: {result['confidence']:.2%}")
                    else:
                        st.error(f"❌ Transcription failed: {result['error']}")
                        st.session_state.audio_processing_status = "error"
        
        with col2:
            # Only enable AI response if we have a transcription
            ai_disabled = not st.session_state.last_transcription
            
            if st.button("🤖 Get AI Response", disabled=ai_disabled):
                if st.session_state.last_transcription:
                    with st.spinner("Getting AI response..."):
                        try:
                            response = process_query(
                                st.session_state.last_transcription, 
                                ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"], 
                                True, 
                                "text"
                            )
                            
                            st.markdown("### 🤖 AI Response:")
                            st.markdown(response["content"])
                            
                            # Display processing metrics
                            col_metrics1, col_metrics2 = st.columns(2)
                            with col_metrics1:
                                if response.get("processing_time"):
                                    st.metric("Processing Time", f"{response['processing_time']:.2f}s")
                            with col_metrics2:
                                if response.get("confidence", 0) > 0:
                                    st.metric("Confidence", f"{response['confidence']:.1%}")
                            
                            # Voice response option
                            if st.checkbox("🔊 Generate Voice Response", key="voice_response_check"):
                                with st.spinner("Generating voice response..."):
                                    voice_result = synthesize_speech(response["content"])
                                    
                                    if voice_result["success"]:
                                        st.success("🎵 Voice response generated!")
                                        st.audio(voice_result["audio_data"], format="audio/mp3")
                                    else:
                                        st.error(f"Voice synthesis failed: {voice_result['error']}")
                                        
                        except Exception as e:
                            st.error(f"❌ Error getting AI response: {str(e)}")
                else:
                    st.warning("⚠️ Please transcribe an audio file first.")
    
    # Display last transcription if available
    if st.session_state.last_transcription:
        st.markdown("### 📝 Current Transcription:")
        st.text_area(
            "Last transcribed text:", 
            value=st.session_state.last_transcription, 
            height=80, 
            disabled=True,
            key="last_transcription_display"
        )
        
        # Clear transcription button
        if st.button("🗑️ Clear Transcription"):
            st.session_state.last_transcription = ""
            st.session_state.audio_processing_status = "idle"
            st.rerun()
    
    # Instructions
    st.markdown("---")
    st.markdown("### 📋 How to Use:")
    st.markdown("""
    1. **📁 Upload an audio file** using the file uploader above
    2. **🔄 Click "Process Audio File"** to transcribe the audio to text
    3. **🤖 Click "Get AI Response"** to analyze the transcription with the finance assistant
    4. **🔊 Optionally enable voice response** to hear the AI's answer
    
    **💡 Tips:**
    - Speak clearly and avoid background noise for best transcription results
    - Files under 25MB process faster
    - Supported formats: WAV, MP3, M4A, MP4, MPEG, MPGA, WebM
    """)
    
    # Text-to-Speech section
    st.markdown("---")
    st.subheader("🔊 Text-to-Speech")
    
    col_tts1, col_tts2 = st.columns([3, 1])
    
    with col_tts1:
        text_to_speak = st.text_area(
            "Enter text to convert to speech:", 
            height=100,
            placeholder="Type your text here..."
        )
    
    with col_tts2:
        voice_options = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        selected_voice = st.selectbox("Voice:", voice_options, index=0)
    
    if st.button("🎵 Generate Speech", disabled=not text_to_speak.strip()):
        with st.spinner("Generating speech..."):
            result = synthesize_speech(text_to_speak.strip(), selected_voice)
            
            if result["success"]:
                st.success("✅ Speech generated successfully!")
                st.audio(result["audio_data"], format="audio/mp3")
            else:
                st.error(f"❌ Speech generation failed: {result['error']}")

def main():
    """Main chat interface"""
    st.markdown('<h1 class="main-header">🤖 Multi-Agent Finance Assistant</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()

    with st.sidebar:
        st.header("🔧 Configuration")
        
        st.subheader("Agent Status")
        if st.button("🔄 Refresh Status"):
            st.rerun()
        check_agent_health()
        
        st.subheader("Settings")
        include_analysis = st.checkbox("Include Analysis", value=True)
        response_type = st.selectbox("Response Type", ["text", "voice"])
        
        st.subheader("Stock Symbols")
        default_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
        symbols_input = st.text_area(
            "Enter symbols (one per line)",
            value="\n".join(default_symbols),
            help="Add stock symbols you want to monitor"
        )
        symbols = [s.strip().upper() for s in symbols_input.split('\n') if s.strip()]
        
        # Display current symbols
        if symbols:
            st.caption(f"Monitoring: {', '.join(symbols)}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat Interface")

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about your portfolio or market conditions..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate assistant response
            with st.chat_message("assistant"):
                with st.spinner("Processing your request..."):
                    response = process_query(prompt, symbols, include_analysis, response_type)
                    st.markdown(response["content"])

                    # Voice response if enabled
                    if response_type == "voice" and response["content"]:
                        with st.spinner("Generating voice response..."):
                            voice_result = synthesize_speech(response["content"])
                            if voice_result["success"]:
                                st.audio(voice_result["audio_data"], format="audio/mp3")
                            else:
                                st.error(f"Voice synthesis failed: {voice_result['error']}")

                    # Display metrics
                    col_metrics1, col_metrics2 = st.columns(2)
                    with col_metrics1:
                        processing_time = response.get("processing_time")
                        if processing_time:
                            st.caption(f"⏱️ Processed in {processing_time:.2f}s")
                    
                    with col_metrics2:
                        if response.get("confidence", 0) > 0:
                            st.caption(f"🎯 Confidence: {response['confidence']:.2%}")

            # Add assistant message to history
            st.session_state.messages.append({"role": "assistant", "content": response["content"]})

    with col2:
        st.header("🔄 Quick Actions")
        
        quick_queries = [
            "What's our risk exposure in tech stocks today?",
            "Show me the performance of my portfolio",
            "Any earnings surprises in my holdings?",
            "What's the market sentiment today?",
            "Analyze the volatility of tech stocks",
            "Give me a market summary"
        ]
        
        for i, query in enumerate(quick_queries):
            if st.button(query, key=f"quick_{i}"):
                with st.spinner("Processing..."):
                    response = process_query(query, symbols, include_analysis, "text")
                    
                    # Add to chat history
                    st.session_state.messages.append({"role": "user", "content": query})
                    st.session_state.messages.append({"role": "assistant", "content": response["content"]})
                    
                    # Show response
                    st.success("Response added to chat!")
                    st.rerun()
        
        # Clear chat button
        st.markdown("---")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

def system_status():
    """System status page"""
    st.header("🔧 System Status")
    
    # Agent health check
    st.subheader("🏥 Agent Health Status")
    check_agent_health()
    
    # System metrics (placeholder)
    st.subheader("📊 Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Sessions", "1", delta="0")
    
    with col2:
        st.metric("Avg Response Time", "2.3s", delta="-0.5s")
    
    with col3:
        st.metric("Success Rate", "98.5%", delta="1.2%")
    
    # Configuration display
    st.subheader("⚙️ Configuration")
    
    config_data = {
        "Orchestrator URL": ORCHESTRATOR_URL,
        "Agent Count": len(AGENT_URLS),
        "Session State Size": len(st.session_state) if hasattr(st, 'session_state') else 0
    }
    
    for key, value in config_data.items():
        st.text(f"{key}: {value}")
    
    # Agent URLs
    st.subheader("🔗 Service Endpoints")
    for agent_name, url in AGENT_URLS.items():
        st.text(f"{agent_name.title()}: {url}")

def run_app():
    """Main application runner"""
    # Navigation
    page = st.sidebar.selectbox(
        "📍 Navigation", 
        ["Main Chat", "Voice Interface", "System Status"],
        help="Select the interface you want to use"
    )
    
    # Route to appropriate page
    if page == "Main Chat":
        main()
    elif page == "Voice Interface":
        voice_interface()
    elif page == "System Status":
        system_status()

if __name__ == "__main__":
    run_app()