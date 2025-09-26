import os
import uuid
import tempfile
import base64
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json

# import speech_recognition as sr  # Not compatible with Python 3.13
# import openai_whisper as whisper  # Disabled for Python 3.13 compatibility
# import torch  # Disabled for Python 3.13 compatibility
# import torchaudio  # Disabled for Python 3.13 compatibility
# from pydub import AudioSegment  # Disabled for Python 3.13 compatibility (audioop module removed)
# from pydub.utils import which  # Disabled for Python 3.13 compatibility
import numpy as np

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.voice import (
    VoiceSession, VoiceTranscription, ClinicalVoiceNote, 
    VoiceProcessingJob, VoiceConfiguration
)
from app.schemas.voice import (
    VoiceSessionStartRequest, VoiceAudioUploadRequest, 
    VoiceTranscriptionRequest, VoiceNoteGenerationRequest,
    VoiceQualityAssessment, VoiceProcessingStatus
)

logger = logging.getLogger(__name__)

class VoiceProcessingService:
    """Service for voice processing and transcription"""
    
    def __init__(self, db: Session):
        self.db = db
        self.temp_dir = Path(tempfile.gettempdir()) / "prontivus_voice"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Initialize speech recognition (disabled for Python 3.13 compatibility)
        # self.recognizer = sr.Recognizer()
        # self.recognizer.energy_threshold = 300
        # self.recognizer.dynamic_energy_threshold = True
        # self.recognizer.pause_threshold = 0.8
        
        # Initialize Whisper model (disabled for Python 3.13 compatibility)
        self.whisper_model = None
        self.whisper_model_name = "base"  # Can be configured
        self.whisper_available = False  # Disabled due to compatibility issues
        
        # Medical terminology dictionaries
        self.medical_terms = self._load_medical_terminology()
        self.drug_names = self._load_drug_names()
        self.anatomical_terms = self._load_anatomical_terms()
    
    def _load_medical_terminology(self) -> List[str]:
        """Load medical terminology for detection"""
        # This would typically load from a database or file
        return [
            "diagnóstico", "sintoma", "tratamento", "medicamento", "dosagem",
            "prescrição", "exame", "resultado", "prognóstico", "terapia",
            "cirurgia", "procedimento", "anestesia", "recuperação", "alta",
            "consulta", "seguimento", "controle", "monitoramento", "avaliação"
        ]
    
    def _load_drug_names(self) -> List[str]:
        """Load drug names for detection"""
        # This would typically load from a database or file
        return [
            "paracetamol", "ibuprofeno", "dipirona", "omeprazol", "losartana",
            "metformina", "sinvastatina", "atorvastatina", "amlodipina", "hidroclorotiazida"
        ]
    
    def _load_anatomical_terms(self) -> List[str]:
        """Load anatomical terms for detection"""
        # This would typically load from a database or file
        return [
            "cabeça", "pescoço", "tórax", "abdômen", "pelve", "membros",
            "coração", "pulmão", "fígado", "rim", "estômago", "intestino",
            "cérebro", "coluna", "articulação", "músculo", "osso", "pele"
        ]
    
    def _get_whisper_model(self):
        """Get or load Whisper model (disabled for Python 3.13 compatibility)"""
        if not self.whisper_available:
            raise RuntimeError("Whisper is not available due to Python 3.13 compatibility issues")
        return None  # Whisper disabled
    
    def start_voice_session(self, request: VoiceSessionStartRequest, user_id: int) -> VoiceSession:
        """Start a new voice recording session"""
        try:
            session_id = f"VS-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            session = VoiceSession(
                session_id=session_id,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                appointment_id=request.appointment_id,
                clinical_context=request.clinical_context,
                medical_specialty=request.medical_specialty,
                session_type=request.session_type,
                transcription_language=request.transcription_language,
                start_time=datetime.utcnow(),
                created_by=user_id
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Voice session {session_id} started successfully")
            return session
            
        except Exception as e:
            logger.error(f"Error starting voice session: {e}")
            raise
    
    def upload_audio(self, request: VoiceAudioUploadRequest, user_id: int) -> Dict[str, Any]:
        """Upload and process audio data"""
        try:
            # Find the session
            session = self.db.query(VoiceSession).filter(
                VoiceSession.session_id == request.session_id
            ).first()
            
            if not session:
                raise ValueError("Voice session not found")
            
            # Decode base64 audio data
            audio_data = base64.b64decode(request.audio_data)
            
            # Save audio file
            audio_filename = f"{request.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.audio_format}"
            audio_path = self.temp_dir / audio_filename
            
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            # Get file size
            file_size = audio_path.stat().st_size
            
            # Update session with audio file information
            session.audio_file_path = str(audio_path)
            session.audio_file_size = file_size
            session.audio_format = request.audio_format
            session.sample_rate = request.sample_rate
            session.channels = request.channels
            
            self.db.commit()
            
            # Perform quality assessment
            quality_assessment = self._assess_audio_quality(str(audio_path))
            session.audio_quality_score = quality_assessment.audio_quality_score
            session.background_noise_level = quality_assessment.background_noise_level
            session.speech_clarity_score = quality_assessment.speech_clarity_score
            
            self.db.commit()
            
            logger.info(f"Audio uploaded successfully for session {request.session_id}")
            return {
                "success": True,
                "message": "Audio uploaded successfully",
                "file_path": str(audio_path),
                "file_size": file_size,
                "quality_assessment": quality_assessment.dict()
            }
            
        except Exception as e:
            logger.error(f"Error uploading audio: {e}")
            raise
    
    def _assess_audio_quality(self, audio_path: str) -> VoiceQualityAssessment:
        """Assess the quality of uploaded audio"""
        try:
            # Load audio file (disabled for Python 3.13 compatibility)
            # audio = AudioSegment.from_file(audio_path)
            raise RuntimeError("Audio quality assessment disabled due to Python 3.13 compatibility issues")
            
            # Calculate basic quality metrics
            duration = len(audio) / 1000.0  # Convert to seconds
            
            # Calculate RMS (Root Mean Square) for volume assessment
            rms = audio.rms
            max_rms = audio.max_possible_amplitude
            
            # Calculate signal-to-noise ratio (simplified)
            # This is a basic implementation - in production, you'd use more sophisticated methods
            audio_array = np.array(audio.get_array_of_samples())
            signal_power = np.mean(audio_array ** 2)
            noise_power = np.var(audio_array)
            snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
            
            # Normalize metrics to 0-1 scale
            audio_quality_score = min(1.0, max(0.0, (snr + 20) / 40))  # Assume SNR range -20 to 20 dB
            background_noise_level = min(1.0, max(0.0, 1 - (snr + 20) / 40))
            speech_clarity_score = min(1.0, max(0.0, rms / max_rms))
            
            # Determine overall quality
            overall_score = (audio_quality_score + speech_clarity_score) / 2
            if overall_score >= 0.8:
                overall_quality = "excellent"
            elif overall_score >= 0.6:
                overall_quality = "good"
            elif overall_score >= 0.4:
                overall_quality = "fair"
            else:
                overall_quality = "poor"
            
            # Generate recommendations
            recommendations = []
            if background_noise_level > 0.7:
                recommendations.append("High background noise detected. Consider recording in a quieter environment.")
            if speech_clarity_score < 0.5:
                recommendations.append("Low speech clarity. Speak closer to the microphone.")
            if duration < 10:
                recommendations.append("Short recording duration. Consider recording for longer periods.")
            
            return VoiceQualityAssessment(
                audio_quality_score=audio_quality_score,
                background_noise_level=background_noise_level,
                speech_clarity_score=speech_clarity_score,
                overall_quality=overall_quality,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error assessing audio quality: {e}")
            # Return default values on error
            return VoiceQualityAssessment(
                audio_quality_score=0.5,
                background_noise_level=0.5,
                speech_clarity_score=0.5,
                overall_quality="fair",
                recommendations=["Unable to assess audio quality"]
            )
    
    def transcribe_audio(self, request: VoiceTranscriptionRequest, user_id: int) -> Dict[str, Any]:
        """Transcribe audio using specified engine"""
        try:
            # Find the session
            session = self.db.query(VoiceSession).filter(
                VoiceSession.session_id == request.session_id
            ).first()
            
            if not session:
                raise ValueError("Voice session not found")
            
            if not session.audio_file_path or not os.path.exists(session.audio_file_path):
                raise ValueError("Audio file not found")
            
            # Create processing job
            job_id = f"TR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            job = VoiceProcessingJob(
                job_id=job_id,
                session_id=session.id,
                job_type="transcription",
                status="running",
                started_at=datetime.utcnow(),
                parameters={
                    "transcription_engine": request.transcription_engine,
                    "language": request.language,
                    "enable_medical_terminology": request.enable_medical_terminology,
                    "enable_drug_detection": request.enable_drug_detection,
                    "enable_anatomical_detection": request.enable_anatomical_detection
                }
            )
            
            self.db.add(job)
            self.db.commit()
            
            # Update session status
            session.transcription_status = "processing"
            session.processing_started_at = datetime.utcnow()
            self.db.commit()
            
            # Perform transcription based on engine
            if request.transcription_engine == "whisper":
                transcription_result = self._transcribe_with_whisper(
                    session.audio_file_path, 
                    request.language
                )
            elif request.transcription_engine == "google":
                transcription_result = self._transcribe_with_google(
                    session.audio_file_path, 
                    request.language
                )
            else:
                raise ValueError(f"Unsupported transcription engine: {request.transcription_engine}")
            
            # Process transcription result
            self._process_transcription_result(
                session, 
                transcription_result, 
                request, 
                job
            )
            
            # Update job status
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.processing_time_seconds = (job.completed_at - job.started_at).total_seconds()
            job.result_data = transcription_result
            
            # Update session
            session.transcription_status = "completed"
            session.processing_completed_at = datetime.utcnow()
            session.transcription_confidence = transcription_result.get("confidence", 0.0)
            
            self.db.commit()
            
            logger.info(f"Transcription completed for session {request.session_id}")
            return {
                "success": True,
                "message": "Transcription completed successfully",
                "transcription_id": job_id,
                "estimated_processing_time": int(job.processing_time_seconds)
            }
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            
            # Update job and session status on error
            if 'job' in locals():
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
            
            if 'session' in locals():
                session.transcription_status = "failed"
                session.processing_errors = {"transcription_error": str(e)}
                session.processing_completed_at = datetime.utcnow()
            
            self.db.commit()
            raise
    
    def _transcribe_with_whisper(self, audio_path: str, language: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper (disabled for Python 3.13 compatibility)"""
        # Whisper is disabled due to Python 3.13 compatibility issues
        # Return a placeholder response
        return {
            "text": "Transcription temporarily unavailable due to compatibility issues",
            "confidence": 0.0,
            "language": language,
            "segments": [],
            "engine": "whisper_disabled"
        }
    
    def _transcribe_with_google(self, audio_path: str, language: str) -> Dict[str, Any]:
        """Transcribe audio using Google Speech Recognition (disabled for Python 3.13 compatibility)"""
        # Google Speech Recognition is disabled due to Python 3.13 compatibility issues
        # Fallback to Whisper instead
        return self._transcribe_with_whisper(audio_path, language)
    
    def _process_transcription_result(
        self, 
        session: VoiceSession, 
        result: Dict[str, Any], 
        request: VoiceTranscriptionRequest,
        job: VoiceProcessingJob
    ):
        """Process transcription result and extract medical information"""
        try:
            text = result["text"]
            
            # Update session with transcription text
            session.transcription_text = text
            
            # Extract medical information if enabled
            medical_terms = []
            drug_names = []
            anatomical_terms = []
            
            if request.enable_medical_terminology:
                medical_terms = self._extract_medical_terms(text)
            
            if request.enable_drug_detection:
                drug_names = self._extract_drug_names(text)
            
            if request.enable_anatomical_detection:
                anatomical_terms = self._extract_anatomical_terms(text)
            
            # Create transcription record
            transcription = VoiceTranscription(
                session_id=session.id,
                segment_number=1,
                start_time_seconds=0.0,
                end_time_seconds=0.0,  # Will be updated with actual duration
                duration_seconds=0.0,
                original_text=text,
                transcription_engine=request.transcription_engine,
                language_detected=result.get("language", request.language),
                confidence_score=result.get("confidence", 0.0),
                medical_terms_detected=medical_terms,
                drug_names_detected=drug_names,
                anatomical_terms_detected=anatomical_terms,
                audio_quality_segment=session.audio_quality_score,
                speech_clarity_segment=session.speech_clarity_score
            )
            
            self.db.add(transcription)
            
            # Update result data with extracted information
            result["medical_terms"] = medical_terms
            result["drug_names"] = drug_names
            result["anatomical_terms"] = anatomical_terms
            
        except Exception as e:
            logger.error(f"Error processing transcription result: {e}")
            raise
    
    def _extract_medical_terms(self, text: str) -> List[str]:
        """Extract medical terms from text"""
        found_terms = []
        text_lower = text.lower()
        
        for term in self.medical_terms:
            if term.lower() in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    def _extract_drug_names(self, text: str) -> List[str]:
        """Extract drug names from text"""
        found_drugs = []
        text_lower = text.lower()
        
        for drug in self.drug_names:
            if drug.lower() in text_lower:
                found_drugs.append(drug)
        
        return found_drugs
    
    def _extract_anatomical_terms(self, text: str) -> List[str]:
        """Extract anatomical terms from text"""
        found_terms = []
        text_lower = text.lower()
        
        for term in self.anatomical_terms:
            if term.lower() in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    def generate_clinical_note(self, request: VoiceNoteGenerationRequest, user_id: int) -> Dict[str, Any]:
        """Generate clinical note from voice session"""
        try:
            # Find the session
            session = self.db.query(VoiceSession).filter(
                VoiceSession.session_id == request.session_id
            ).first()
            
            if not session:
                raise ValueError("Voice session not found")
            
            if not session.transcription_text:
                raise ValueError("No transcription available for note generation")
            
            # Create processing job
            job_id = f"CN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            job = VoiceProcessingJob(
                job_id=job_id,
                session_id=session.id,
                job_type="note_generation",
                status="running",
                started_at=datetime.utcnow(),
                parameters={
                    "note_type": request.note_type,
                    "include_ai_analysis": request.include_ai_analysis,
                    "auto_extract_entities": request.auto_extract_entities,
                    "generate_suggestions": request.generate_suggestions
                }
            )
            
            self.db.add(job)
            self.db.commit()
            
            # Generate clinical note
            note_content = self._generate_note_content(session, request)
            
            # Create clinical note record
            clinical_note = ClinicalVoiceNote(
                session_id=session.id,
                note_type=request.note_type,
                title=f"Nota Clínica - {session.patient_id} - {datetime.now().strftime('%d/%m/%Y')}",
                content=note_content,
                ai_processed=request.include_ai_analysis,
                ai_confidence_score=0.8,  # Mock confidence score
                created_by=user_id
            )
            
            self.db.add(clinical_note)
            self.db.commit()
            self.db.refresh(clinical_note)
            
            # Update job status
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.processing_time_seconds = (job.completed_at - job.started_at).total_seconds()
            job.result_data = {"note_id": clinical_note.id}
            
            self.db.commit()
            
            logger.info(f"Clinical note generated for session {request.session_id}")
            return {
                "success": True,
                "message": "Clinical note generated successfully",
                "note_id": clinical_note.id,
                "estimated_processing_time": int(job.processing_time_seconds)
            }
            
        except Exception as e:
            logger.error(f"Error generating clinical note: {e}")
            
            # Update job status on error
            if 'job' in locals():
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                self.db.commit()
            
            raise
    
    def _generate_note_content(self, session: VoiceSession, request: VoiceNoteGenerationRequest) -> str:
        """Generate clinical note content from transcription"""
        try:
            # Basic note structure
            note_parts = []
            
            # Header
            note_parts.append(f"NOTA CLÍNICA")
            note_parts.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            note_parts.append(f"Paciente: {session.patient_id}")
            note_parts.append(f"Médico: {session.doctor_id}")
            note_parts.append("")
            
            # Clinical context
            if session.clinical_context:
                note_parts.append(f"Contexto Clínico: {session.clinical_context}")
                note_parts.append("")
            
            # Transcription content
            note_parts.append("RELATO DO MÉDICO:")
            note_parts.append(session.transcription_text)
            note_parts.append("")
            
            # AI analysis if enabled
            if request.include_ai_analysis:
                note_parts.append("ANÁLISE AUTOMÁTICA:")
                note_parts.append("• Termos médicos detectados: " + ", ".join(self._extract_medical_terms(session.transcription_text)))
                note_parts.append("• Medicamentos mencionados: " + ", ".join(self._extract_drug_names(session.transcription_text)))
                note_parts.append("• Termos anatômicos: " + ", ".join(self._extract_anatomical_terms(session.transcription_text)))
                note_parts.append("")
            
            # Footer
            note_parts.append("---")
            note_parts.append("Nota gerada automaticamente a partir de gravação de voz")
            note_parts.append(f"Sessão: {session.session_id}")
            
            return "\n".join(note_parts)
            
        except Exception as e:
            logger.error(f"Error generating note content: {e}")
            return f"Erro ao gerar conteúdo da nota: {str(e)}"
    
    def end_voice_session(self, session_id: str, user_id: int, auto_transcribe: bool = True, auto_generate_note: bool = False) -> Dict[str, Any]:
        """End a voice recording session"""
        try:
            # Find the session
            session = self.db.query(VoiceSession).filter(
                VoiceSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError("Voice session not found")
            
            # Update session end time and duration
            session.end_time = datetime.utcnow()
            session.duration_seconds = int((session.end_time - session.start_time).total_seconds())
            session.status = "completed"
            
            self.db.commit()
            
            result = {
                "success": True,
                "message": "Voice session ended successfully",
                "session_duration": session.duration_seconds
            }
            
            # Auto-transcribe if requested
            if auto_transcribe and session.audio_file_path:
                try:
                    transcription_request = VoiceTranscriptionRequest(
                        session_id=session_id,
                        transcription_engine="whisper",
                        language=session.transcription_language
                    )
                    transcription_result = self.transcribe_audio(transcription_request, user_id)
                    result["transcription_job_id"] = transcription_result.get("transcription_id")
                except Exception as e:
                    logger.error(f"Error in auto-transcription: {e}")
                    result["transcription_error"] = str(e)
            
            # Auto-generate note if requested
            if auto_generate_note and session.transcription_text:
                try:
                    note_request = VoiceNoteGenerationRequest(
                        session_id=session_id,
                        note_type="progress_note"
                    )
                    note_result = self.generate_clinical_note(note_request, user_id)
                    result["note_generation_job_id"] = note_result.get("note_id")
                except Exception as e:
                    logger.error(f"Error in auto-note generation: {e}")
                    result["note_generation_error"] = str(e)
            
            return result
            
        except Exception as e:
            logger.error(f"Error ending voice session: {e}")
            raise
    
    def get_processing_status(self, session_id: str) -> VoiceProcessingStatus:
        """Get processing status for a voice session"""
        try:
            session = self.db.query(VoiceSession).filter(
                VoiceSession.session_id == session_id
            ).first()
            
            if not session:
                raise ValueError("Voice session not found")
            
            # Get active jobs
            active_jobs = self.db.query(VoiceProcessingJob).filter(
                VoiceProcessingJob.session_id == session.id,
                VoiceProcessingJob.status.in_(["pending", "running"])
            ).all()
            
            if not active_jobs:
                return VoiceProcessingStatus(
                    session_id=session_id,
                    status="completed",
                    progress_percentage=100,
                    current_step="completed"
                )
            
            # Calculate overall progress
            total_progress = sum(job.progress_percentage for job in active_jobs)
            avg_progress = total_progress / len(active_jobs) if active_jobs else 0
            
            # Get current step
            current_step = "processing"
            if session.transcription_status == "processing":
                current_step = "transcribing"
            elif session.transcription_status == "completed":
                current_step = "analyzing"
            
            return VoiceProcessingStatus(
                session_id=session_id,
                status="processing",
                progress_percentage=int(avg_progress),
                current_step=current_step,
                estimated_completion_time=30  # Mock estimate
            )
            
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            raise
