import streamlit as st
import whisper
import qrcode
import librosa
import numpy as np
import os
from tempfile import NamedTemporaryFile
from io import BytesIO
from PIL import Image

# For real-time microphone transcription
# pip install streamlit-webrtc
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av

st.set_page_config(page_title="SafeSound+", page_icon="🎧")
st.title("🎧 SafeSound+")

# ----------------------
# GLOBALS & CONFIG
# ----------------------
if "transcription" not in st.session_state:
    st.session_state.transcription = ""
if "audio_stats" not in st.session_state:
    st.session_state.audio_stats = {}
if "buffer" not in st.session_state:
    st.session_state.buffer = b""  # For live audio frames

# Language map: user-friendly name -> whisper code
LANG_MAP = {
    "Auto": None,
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko"
}

# ICE config for WebRTC
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# ----------------------
# SIDEBAR CONTROLS
# ----------------------
with st.sidebar:
    st.header("Controls")
    # Whisper model selection
    model_options = ["tiny", "base", "small", "medium", "large"]
    selected_model = st.selectbox("Choose Whisper Model", model_options, index=1)
    
    # Source language selection
    lang_options = list(LANG_MAP.keys())
    selected_language_name = st.selectbox("Select Source Language", lang_options, index=0)
    selected_language_code = LANG_MAP[selected_language_name]  # None if "Auto"
    
    # Task: transcribe or translate
    task_options = ["Transcribe (same language)", "Translate to English"]
    selected_task = st.selectbox("Task", task_options, index=0)
    if selected_task == "Transcribe (same language)":
        task = "transcribe"
    else:
        task = "translate"  # Whisper will produce English
    
    # Choose input type: file upload or microphone
    input_type = st.radio("Input Type", ["File Upload", "Microphone"])
    
    transcribe_button = st.button("Transcribe Audio")
    
    st.header("Original Audio")
    audio_player = st.empty()

# ----------------------
# HELPER FUNCTIONS
# ----------------------
def save_temp_file(audio_file):
    """Save uploaded file to a temp location and return path."""
    with NamedTemporaryFile(delete=False, suffix=audio_file.name) as tmp:
        tmp.write(audio_file.getbuffer())
        return tmp.name

def transcribe_audio(model, audio_path, language_code=None, task="transcribe"):
    """
    Transcribe/translate audio using Whisper model.
    If language_code is None, it auto-detects.
    If task='translate', the output is always in English.
    """
    if language_code:
        result = model.transcribe(audio_path, language=language_code, task=task)
    else:
        result = model.transcribe(audio_path, task=task)
    return result["text"]

def calculate_audio_stats(audio_path, transcription):
    """Calculate audio duration, word count, speaking speed."""
    duration = librosa.get_duration(filename=audio_path)
    word_count = len(transcription.split())
    speaking_speed = word_count / (duration / 60) if duration > 0 else 0
    return {
        "duration": duration,
        "word_count": word_count,
        "speaking_speed": speaking_speed
    }

def generate_qr_code(text):
    """Generate QR code from text."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def download_transcription_text_button(transcription: str, filename="transcription.txt"):
    """
    Provide a download button for a text transcription.
    """
    st.download_button(
        label="Download as TXT",
        data=transcription,
        file_name=filename,
        mime="text/plain"
    )

# ----------------------
# MAIN APP LOGIC
# ----------------------

# 1) FILE UPLOAD MODE
temp_path = None
audio_file = None

if input_type == "File Upload":
    audio_file = st.file_uploader("Upload Audio File", type=["wav", "mp3", "m4a", "ogg"])
    if audio_file:
        temp_path = save_temp_file(audio_file)
        # Show audio player
        audio_player.audio(temp_path)

# 2) MICROPHONE MODE (Real-Time)
#    We use streamlit-webrtc to capture audio and transcribe in near real-time
if input_type == "Microphone":
    st.write("#### Microphone Capture (Experimental)")

    # WebRTC streamer
    def audio_callback(frame: av.AudioFrame) -> av.AudioFrame:
        """
        Receives audio frames from microphone in real-time.
        We'll buffer them in memory so we can do a transcription
        once the user clicks "Transcribe Audio."
        """
        # Convert to bytes
        audio_data = np.array(frame.to_ndarray(), dtype=np.float32)
        # We might want to store raw PCM data in st.session_state.buffer
        # However, this would be uncompressed PCM. Whisper can handle WAV/MP3, but not raw frames directly.
        # For a "quick hack," we can do an in-memory WAV file each time user hits 'Transcribe Audio.'
        # So let's keep appending frames:
        st.session_state.buffer += audio_data.tobytes()
        return frame  # pass it downstream if needed
    
    webrtc_ctx = webrtc_streamer(
        key="microphone",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=256,  # the chunk size
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"audio": True, "video": False},
        audio_frame_callback=audio_callback,
    )
    
    if webrtc_ctx.state.playing:
        st.write("Recording... press 'Transcribe Audio' when you're done.")
    else:
        st.write("Click 'Start' above to begin recording from mic.")

# ----------------------
# TRANSCRIBE BUTTON LOGIC
# ----------------------
if transcribe_button:
    # If microphone, create a temporary WAV from the session buffer
    if input_type == "Microphone":
        if len(st.session_state.buffer) == 0:
            st.sidebar.error("No microphone audio captured yet!")
        else:
            with st.spinner("Preparing microphone audio for transcription..."):
                # Save st.session_state.buffer as a WAV file
                mic_temp = NamedTemporaryFile(delete=False, suffix=".wav")
                mic_temp.write(st.session_state.buffer)
                mic_temp.flush()
                mic_temp_path = mic_temp.name
                mic_temp.close()
                temp_path = mic_temp_path
    
    # If still no temp_path (no file uploaded or no mic audio), show error
    if not temp_path:
        st.sidebar.error("Please provide audio input first!")
    else:
        try:
            with st.spinner("Loading Whisper model..."):
                model = whisper.load_model(selected_model)
            
            st.subheader("Transcription Result")
            
            with st.spinner("Transcribing audio..."):
                transcription = transcribe_audio(
                    model=model,
                    audio_path=temp_path,
                    language_code=selected_language_code,
                    task=task
                )
                st.session_state.transcription = transcription
                
                # Calculate audio statistics
                st.session_state.audio_stats = calculate_audio_stats(temp_path, transcription)
            
            st.success("Transcription complete!")
            
            # Display statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Duration", f"{st.session_state.audio_stats['duration']/60:.2f} mins")
            with col2:
                st.metric("Word Count", st.session_state.audio_stats["word_count"])
            with col3:
                st.metric("Speaking Speed", f"{st.session_state.audio_stats['speaking_speed']:.1f} wpm")
            
            # Transcription text + copy button
            st.write("Transcription Text:")
            copy_col, text_col = st.columns([0.1, 0.9])
            with copy_col:
                if st.button("📋", help="Copy to clipboard"):
                    js_code = f"""
                    <script>
                    function copyText() {{
                        navigator.clipboard.writeText(`{st.session_state.transcription}`);
                    }}
                    copyText();
                    </script>
                    """
                    st.components.v1.html(js_code)
            with text_col:
                st.write(st.session_state.transcription)
            
            # Download as TXT
            download_transcription_text_button(st.session_state.transcription)
            
            # # QR Code Generation
            # st.subheader("Share via QR Code")
            # qr_img = generate_qr_code(st.session_state.transcription)
            # # Convert QR code to bytes for download
            # img_byte_arr = BytesIO()
            # qr_img.save(img_byte_arr, format='PNG')
            # img_byte_arr = img_byte_arr.getvalue()
            
            # qr_col1, qr_col2 = st.columns([0.3, 0.7])
            # with qr_col1:
            #     st.image(qr_img, caption="Transcription QR Code", use_column_width=True)
            # with qr_col2:
            #     st.download_button(
            #         label="Download QR Code",
            #         data=img_byte_arr,
            #         file_name="transcription_qr.png",
            #         mime="image/png"
            #     )
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
        finally:
            # Clean up microphone buffer if we used it
            if input_type == "Microphone":
                st.session_state.buffer = b""
            # Clean up temp file
            if 'temp_path' in locals() and temp_path is not None:
                try:
                    os.remove(temp_path)
                except:
                    pass
