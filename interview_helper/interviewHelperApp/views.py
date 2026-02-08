from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.models import User,auth
from django.contrib import messages
from django.db.models import Q, F
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.encoding import smart_str
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import CommunityQuestion

import logging
import json
import re
import sys
import os
import tempfile
import time
from pathlib import Path

import requests


# Gemini AI imports - CORRECT WAY
try:
    from google import genai
    GEMINI_AVAILABLE = True
    print("✓ google.genai imported successfully (new package)")
except ImportError as e:
    print(f"✗ Error importing google.genai: {e}")
    print("  Install with: pip install google-genai")
    GEMINI_AVAILABLE = False
    genai = None

# MoviePy imports
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
    print("✓ moviepy imported successfully")
except ImportError as e:
    print(f"✗ Error importing moviepy: {e}")
    print("  Please install with: pip install moviepy")
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None
    
logger = logging.getLogger(__name__)

# Initialize Gemini client if available
client = None
if GEMINI_AVAILABLE and genai is not None:
    try:
        # Try to get from settings first, then environment variable, then fallback
        GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY', 'AIzaSyBAHtymG7q3CJpYVRmIXdgIruIH8s3SsRY'))
        
        # NEW API for google-genai package
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("✓ Gemini client initialized successfully with new API")
        
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        client = None
else:
    print("⚠ Gemini AI not available - some features will be disabled")

# Create your views here.

def welcome(request):
    return  render(request, 'welcome.html')

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        user = auth.authenticate(username=username, password=password) 
        
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('login')
    else:
        return render(request, 'login.html')
   
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already used')
                return redirect('register')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'username already used ')
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                return redirect('login')
        else:
            messages.info(request, 'password not the same')
            return redirect('register')
    else:
        return render(request, 'register.html')
    
def interview(request):
    # Get question type from URL parameter (default: general)
    question_type = request.GET.get('type', 'general')
    
    # Default fallback questions
    default_questions = {
        'general': "Tell me about yourself and why you're interested in this position.",
        'technical': "Explain a complex technical concept or project you've worked on recently.",
        'behavioral': "Describe a time you faced a significant challenge at work and how you handled it."
    }
    
    # Try to get random question from database
    try:
        question_obj = CommunityQuestion.objects.filter(
            question_type=question_type,
            is_approved=True
        ).order_by('?').first()  # Random question
        
        if question_obj:
            question_text = question_obj.text
            question_source = f"Community Question • {question_obj.vote_count} votes"
        else:
            # No questions in database, use default
            question_text = default_questions.get(question_type, default_questions['general'])
            question_source = "Default Question"
    except:
        # If database error or table doesn't exist yet, use default
        question_text = default_questions.get(question_type, default_questions['general'])
        question_source = "Default Question"
    
    return render(request, 'interview.html', {
        'question': question_text,
        'question_type': question_type,
        'question_source': question_source
    })

def createQuestion(request):
    return render(request, 'createQuestion.html')

#conversion of video to audio
def convert_video_to_audio(video_path, audio_path=None):
    """
    Convert video file to MP3 audio file (kept as fallback)
    Tries MoviePy first, falls back to FFmpeg if needed
    """
    # Create audio path if not provided
    if audio_path is None:
        temp_dir = tempfile.gettempdir()
        timestamp = int(time.time())
        audio_path = os.path.join(temp_dir, f"audio_{timestamp}.mp3")
    
    # Get file extension
    file_ext = os.path.splitext(video_path)[1].lower()
    
    # For WebM files, use FFmpeg directly (more reliable)
    if file_ext == '.webm':
        logger.info("WebM file detected - using FFmpeg directly")
        try:
            return extract_audio_with_ffmpeg(video_path, audio_path)
        except Exception as ffmpeg_error:
            raise RuntimeError(f"WebM conversion failed: {ffmpeg_error}")
    
    # For other formats, try MoviePy first
    if MOVIEPY_AVAILABLE:
        try:
            logger.info(f"Trying MoviePy for: {video_path}")
            video = VideoFileClip(video_path)
            
            video.audio.write_audiofile(
                audio_path, 
                verbose=False, 
                logger=None,
                fps=44100,
                bitrate="192k"
            )
            
            video.close()
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                file_size = os.path.getsize(audio_path)
                logger.info(f"MoviePy extraction successful: {audio_path} ({file_size/1024:.1f} KB)")
                return audio_path
                
        except Exception as moviepy_error:
            logger.warning(f"MoviePy failed: {moviepy_error}")
            # Fall through to FFmpeg
    
    # Fall back to FFmpeg for all other cases
    logger.info("Falling back to FFmpeg extraction")
    return extract_audio_with_ffmpeg(video_path, audio_path)

def extract_audio_with_ffmpeg(video_path, audio_path):
    """
    Extract audio from video using FFmpeg directly
    """
    import subprocess
    
    try:
        logger.info(f"Extracting audio with FFmpeg: {video_path}")
        
        # FFmpeg command to extract audio
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',
            '-acodec', 'libmp3lame',
            '-ab', '192k',
            '-ac', '2',
            '-ar', '44100',
            '-y',
            audio_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg extraction failed: {result.stderr}")
        
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            file_size = os.path.getsize(audio_path)
            logger.info(f"FFmpeg extraction successful: {audio_path} ({file_size/1024:.1f} KB)")
            return audio_path
        else:
            raise RuntimeError("FFmpeg extraction failed - empty output")
            
    except subprocess.TimeoutExpired:
        raise RuntimeError("FFmpeg extraction timed out")
    except Exception as e:
        raise RuntimeError(f"FFmpeg extraction error: {str(e)}")
    
#conversion of audio to text

def home(request):
    return render(request, 'home.html')

def logout(request):    
    auth.logout(request)
    return redirect('start')

# Add these functions after convert_video_to_audio

def get_gemini_feedback_from_video(video_path, question_type="general"):
    """
    Get feedback from Gemini based on the video response directly
    Sends video file to Gemini instead of converting to audio first
    """
    if not GEMINI_AVAILABLE or client is None:
        return "Gemini AI not available. Please check your API key and installation."
    
    # Define prompts
    prompts = {
        "general": """Analyze this video interview response and provide constructive feedback. 
        Your feedback should be in paragraph form only - no headings, no bullet points, no numbered lists, just a single continuous paragraph.
        Focus on: 
        1. Communication clarity and pace
        2. Body language and eye contact (if visible)
        3. Confidence and enthusiasm
        4. Relevance to the question
        5. Areas for improvement
        Be specific and actionable.""",
        
        "technical": """Analyze this technical interview response from the video. 
        Provide feedback on: 
        1. Technical accuracy and knowledge depth
        2. Problem-solving approach and logical thinking
        3. Ability to explain complex concepts clearly
        4. Communication effectiveness
        5. Areas for technical improvement
        Format your response as a single continuous paragraph.""",
        
        "behavioral": """Analyze this behavioral interview response from the video. 
        Provide feedback on: 
        1. STAR method usage (Situation, Task, Action, Result)
        2. Relevance and specificity of examples
        3. Storytelling ability and engagement
        4. Demonstration of soft skills (teamwork, leadership, etc.)
        5. Overall presentation and confidence
        Format your response as a single continuous paragraph."""
    }
    
    prompt = prompts.get(question_type, prompts["general"])
    
    try:
        # Upload the video file directly to Gemini
        print(f"Uploading video file to Gemini: {video_path}")
        uploaded_file = client.files.upload(file=video_path)
        print(f"File uploaded with name: {uploaded_file.name}, initial state: {uploaded_file.state}")
        
        # CRITICAL: Wait for file to be ACTIVE
        print("Waiting for file to process...")
        import time
        
        max_wait_time = 30  # Maximum 30 seconds
        check_interval = 2  # Check every 2 seconds
        wait_time = 0
        
        while wait_time < max_wait_time:
            # Get current file state
            uploaded_file = client.files.get(name=uploaded_file.name)
            current_state = uploaded_file.state
            
            print(f"File state after {wait_time}s: {current_state}")
            
            if current_state.name == "ACTIVE":
                print("✅ File is now ACTIVE and ready to use!")
                break
            elif current_state.name == "FAILED":
                print("❌ File processing failed")
                raise Exception(f"File processing failed: {current_state}")
            
            # Wait and check again
            time.sleep(check_interval)
            wait_time += check_interval
        
        # Check if file is active after waiting
        uploaded_file = client.files.get(name=uploaded_file.name)
        if uploaded_file.state.name != "ACTIVE":
            print(f"⚠️ File still not active after {max_wait_time} seconds")
            raise Exception(f"File processing timed out. State: {uploaded_file.state.name}")
        
        # Generate content with the video file
        print(f"Generating feedback from Gemini for {question_type} question...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                uploaded_file
            ]
        )
        
        print("✅ Feedback generated successfully!")
        return response.text
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"Gemini API error: {e}")
        
        # Check for specific API errors and provide user-friendly messages
        if "PERMISSION_DENIED" in error_str or "403" in error_str:
            if "leaked" in error_str.lower():
                logger.critical("API key reported as leaked!")
                return "AI service configuration issue. Please contact support."
            return "AI service is temporarily unavailable. Please try again later."
        elif "QUOTA_EXCEEDED" in error_str or "429" in error_str:
            return "Service limit reached. Please try again in a few minutes."
        elif "INVALID_ARGUMENT" in error_str or "400" in error_str:
            return "Video format issue. Please try recording again."
        
        # Fallback to audio if video fails
        try:
            print("Video analysis failed, trying audio conversion...")
            return get_gemini_feedback_from_audio_fallback(video_path, question_type)
        except Exception as fallback_error:
            logger.error(f"Audio fallback failed: {fallback_error}")
            return "Unable to analyze your response at this time. Please try again."

@login_required
@csrf_exempt
@require_POST
def analyze_interview(request):
    """Process interview video and get AI feedback directly from video"""
    try:
        if 'video_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No video file provided'}, status=400)
        
        video_file = request.FILES['video_file']
        question_type = request.POST.get('question_type', 'general')
        
        # Accept multiple video formats
        valid_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.wmv']
        original_name = video_file.name
        file_extension = os.path.splitext(original_name)[1].lower()
        
        if file_extension and file_extension not in valid_extensions:
            return JsonResponse({
                'success': False, 
                'error': f'Unsupported file format. Supported formats: {", ".join(valid_extensions)}'
            }, status=400)
        
        # Check file size (max 100MB)
        if video_file.size > 100 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File too large (max 100MB)'}, status=400)
        
        # Check if file has content
        if video_file.size == 0:
            return JsonResponse({'success': False, 'error': 'Empty video file'}, status=400)
        
        # Save video temporarily
        if not file_extension:
            file_extension = '.webm'  # Default for browser recordings
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_video:
            for chunk in video_file.chunks():
                tmp_video.write(chunk)
            video_path = tmp_video.name
        
        logger.info(f"Saved video to: {video_path} (size: {video_file.size} bytes, type: {file_extension})")
        
        try:
            # Get Gemini feedback - try direct video analysis first
            if GEMINI_AVAILABLE and client is not None:
                try:
                    # Try direct video analysis
                    feedback = get_gemini_feedback_from_video(video_path, question_type)
                    analysis_type = 'video_direct'
                    
                except Exception as video_error:
                    logger.warning(f"Direct video analysis failed, trying audio fallback: {video_error}")
                    
                    # Fall back to audio conversion and analysis
                    try:
                        # Convert video to audio first
                        audio_path = convert_video_to_audio(video_path)
                        
                        # Use audio for Gemini analysis
                        feedback = get_gemini_feedback_from_audio(audio_path, question_type)
                        analysis_type = 'audio_fallback'
                        
                        # Clean up audio file
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                            
                    except Exception as audio_error:
                        logger.error(f"Audio fallback also failed: {audio_error}")
                        raise RuntimeError(f"Both video and audio analysis failed: {str(video_error)}")
                        
            else:
                feedback = "Gemini AI not available. Please check your API configuration."
                analysis_type = 'unavailable'
            
            # Clean up temporary video file
            if os.path.exists(video_path):
                os.remove(video_path)
            
            return JsonResponse({
                'success': True,
                'feedback': feedback,
                'question_type': question_type,
                'analysis_type': analysis_type  # Include analysis type in response
            })
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(video_path):
                os.remove(video_path)
            
            error_str = str(e)
            logger.error(f"Processing error: {e}", exc_info=True)
            
            # Determine user-friendly error message
            if "PERMISSION_DENIED" in error_str or "403" in error_str:
                error_message = "AI service is currently unavailable. Please contact support."
            elif "QUOTA_EXCEEDED" in error_str or "429" in error_str:
                error_message = "Service limit reached. Please try again in a few minutes."
            elif "API key" in error_str or "leaked" in error_str.lower():
                error_message = "Configuration issue. Please contact support."
            elif "timeout" in error_str.lower():
                error_message = "Analysis took too long. Please try with a shorter video."
            elif "Both video and audio analysis failed" in error_str:
                error_message = "Unable to process your video. Try recording in a different format."
            else:
                error_message = "Unable to analyze your response. Please try again."
            
            return JsonResponse({
                'success': False, 
                'error': error_message
            }, status=500)
            
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        return JsonResponse({
            'success': False, 
            'error': f'Server error: {str(e)}'
        }, status=500)


@login_required
@require_POST
def tts_feedback(request):
    api_key = getattr(settings, 'ELEVENLABS_API_KEY', os.getenv('ELEVENLABS_API_KEY', '')).strip()
    if not api_key:
        return JsonResponse({
            'success': False,
            'error': 'ElevenLabs API key is not configured.'
        }, status=500)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload.'
        }, status=400)

    text = (payload.get('text') or '').strip()
    if not text:
        return JsonResponse({
            'success': False,
            'error': 'Text is required for speech synthesis.'
        }, status=400)

    # Limit to 500 characters to stay within free tier quota
    if len(text) > 500:
        text = text[:497] + "..."
        logger.info(f"Truncated TTS text to 500 chars to save credits")

    voice_id = getattr(
        settings,
        'ELEVENLABS_VOICE_ID',
        os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')
    )

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    data = {
        'text': text,
        'model_id': 'eleven_multilingual_v2',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
    except requests.RequestException as exc:
        logger.error(f"ElevenLabs request failed: {exc}")
        return JsonResponse({
            'success': False,
            'error': 'TTS provider request failed.'
        }, status=502)

    if response.status_code != 200:
        error_detail = response.text[:200]
        logger.error(
            "ElevenLabs error %s: %s",
            response.status_code,
            error_detail
        )
        
        # Check for quota exceeded
        if "quota_exceeded" in error_detail.lower():
            return JsonResponse({
                'success': False,
                'error': 'Voice synthesis quota exceeded. The feedback text is too long for your current plan.'
            }, status=502)
        
        return JsonResponse({
            'success': False,
            'error': 'TTS provider returned an error.'
        }, status=502)

    return HttpResponse(response.content, content_type='audio/mpeg')
def get_gemini_feedback_from_audio_fallback(video_path, question_type):
    """
    Fallback method: Convert video to audio first, then send to Gemini
    Used if direct video analysis fails
    """
    # Convert video to audio first
    print("Converting video to audio for fallback analysis...")
    audio_path = convert_video_to_audio(video_path)
    print(f"Audio saved to: {audio_path}")
    
    # Define prompts for audio-only analysis
    prompts = {
        "general": "Analyze this audio interview response and provide constructive feedback. Focus on: clarity of communication, pace, confidence level, relevance to the question, and areas for improvement. Be specific and actionable.",
        "technical": "Analyze this technical interview response from the audio. Provide feedback on: technical accuracy, problem-solving approach, communication of complex concepts, and areas for improvement.",
        "behavioral": "Analyze this behavioral interview response from the audio. Provide feedback on: STAR method usage, relevance of examples, storytelling ability, and demonstration of soft skills."
    }
    
    prompt = prompts.get(question_type, prompts["general"])
    
    try:
        print(f"Uploading audio file to Gemini: {audio_path}")
        uploaded_file = client.files.upload(file=audio_path)
        print(f"Audio file uploaded: {uploaded_file.name}, initial state: {uploaded_file.state}")
        
        # Wait for audio file to be ACTIVE
        import time
        max_wait = 30
        wait_time = 0
        
        while wait_time < max_wait:
            uploaded_file = client.files.get(name=uploaded_file.name)
            print(f"Audio file state after {wait_time}s: {uploaded_file.state}")
            
            if uploaded_file.state.name == "ACTIVE":
                print("✅ Audio file is ACTIVE")
                break
            elif uploaded_file.state.name == "FAILED":
                raise Exception(f"Audio file processing failed: {uploaded_file.state}")
            
            time.sleep(2)
            wait_time += 2
        
        uploaded_file = client.files.get(name=uploaded_file.name)
        if uploaded_file.state.name != "ACTIVE":
            raise Exception(f"Audio file processing timed out. State: {uploaded_file.state.name}")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, uploaded_file]
        )
        
        print("✅ Audio analysis successful!")
        
        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Cleaned up audio file: {audio_path}")
            
        return response.text
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise
    
# Add this function after analyze_interview
@csrf_exempt
def system_status(request):
    """Check system status"""
    import subprocess
    
    status = {
        'python_version': sys.version,
        'moviepy_available': MOVIEPY_AVAILABLE,
        'gemini_available': GEMINI_AVAILABLE,
        'ffmpeg_available': False,
        'system_ready': False
    }
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        status['ffmpeg_available'] = result.returncode == 0
    except:
        pass
    
    # Overall status
    status['system_ready'] = (
        status['moviepy_available'] and 
        status['gemini_available'] and 
        status['ffmpeg_available']
    )
    
    return JsonResponse(status)

# Also add the test_gemini_connection function
@csrf_exempt
def test_gemini_connection(request):
    """Test Gemini AI connection"""
    if not GEMINI_AVAILABLE or client is None:
        return JsonResponse({
            'success': False,
            'message': 'Gemini client not initialized'
        })
    
    try:
        # Test with a simple text prompt
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hello, please respond with 'Gemini is working!' and nothing else."
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Gemini API is working',
            'response': response.text
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
        
@login_required
def session_success(request):
    return redirect("home")

@login_required
def session_cancel(request):
    return redirect("home")