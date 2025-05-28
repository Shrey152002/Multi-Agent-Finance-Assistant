import requests
import numpy as np
import io
from scipy.io.wavfile import write

def test_services():
    """Test all backend services individually"""
    
    print("🔍 Testing Backend Services...")
    print("=" * 50)
    
    # Test 1: n8n
    print("1. Testing n8n...")
    try:
        response = requests.get("http://localhost:5678", timeout=5)
        print(f"   ✅ n8n: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ n8n: {e}")
    
    # Test 2: Voice Agent Health
    print("\n2. Testing Voice Agent (port 8006)...")
    try:
        response = requests.get("http://localhost:8006/health", timeout=5)
        print(f"   ✅ Voice Agent Health: Status {response.status_code}")
        print(f"   📝 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Voice Agent Health: {e}")
    
    # Test 3: Orchestrator Health  
    print("\n3. Testing Orchestrator (port 8000)...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"   ✅ Orchestrator Health: Status {response.status_code}")
        print(f"   📝 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Orchestrator Health: {e}")
    
    # Test 4: Voice Agent Transcribe (with dummy audio)
    print("\n4. Testing Voice Agent Transcribe...")
    try:
        # Create a small dummy WAV file
        sample_rate = 44100
        duration = 1  # 1 second
        dummy_audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
        
        wav_io = io.BytesIO()
        audio_int16 = (dummy_audio * 32767).astype(np.int16)
        write(wav_io, sample_rate, audio_int16)
        wav_bytes = wav_io.getvalue()
        
        files = {"file": ("test.wav", wav_bytes, "audio/wav")}
        response = requests.post("http://localhost:8006/transcribe", files=files, timeout=30)
        
        print(f"   ✅ Voice Transcribe: Status {response.status_code}")
        print(f"   📝 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Voice Transcribe: {e}")
    
    # Test 5: Orchestrator Process
    print("\n5. Testing Orchestrator Process...")
    try:
        data = {
            "query": "Hello, this is a test",
            "symbols": [],
            "include_analysis": False,
            "include_news": False,
            "response_type": "brief"
        }
        response = requests.post("http://localhost:8000/process", json=data, timeout=30)
        
        print(f"   ✅ Orchestrator Process: Status {response.status_code}")
        print(f"   📝 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Orchestrator Process: {e}")
    
    # Test 6: Voice Agent Synthesize
    print("\n6. Testing Voice Agent Synthesize...")
    try:
        data = {
            "text": "Hello, this is a test response",
            "voice": "alloy",
            "speed": 1.0
        }
        response = requests.post("http://localhost:8006/synthesize", json=data, timeout=30)
        
        print(f"   ✅ Voice Synthesize: Status {response.status_code}")
        print(f"   📝 Response headers: {dict(response.headers)}")
        print(f"   📝 Response size: {len(response.content)} bytes")
    except Exception as e:
        print(f"   ❌ Voice Synthesize: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Service testing complete!")

if __name__ == "__main__":
    test_services()