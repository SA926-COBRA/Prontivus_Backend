"""
AI Integration Service for Audio-Based Pre-Consultation
Handles audio recording, transcription, and AI analysis for medical consultations
"""

import asyncio
import json
import logging
import uuid
import os
import tempfile
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
import httpx
import openai
from cryptography.fernet import Fernet
import whisper
import torch
from transformers import pipeline

from app.models.ai_integration import (
    AIAnalysisSession, AIAnalysis, AIConfiguration, AIUsageAnalytics, AIPromptTemplate,
    AIProvider, AIAnalysisStatus, AIAnalysisType
)
from app.schemas.ai_integration import (
    AIAnalysisSessionCreate, AIAnalysisSessionUpdate, AIAnalysisSessionInDB,
    AIAnalysisCreate, AIAnalysisUpdate, AIAnalysisInDB,
    AIConfigurationCreate, AIConfigurationUpdate, AIConfigurationInDB,
    AIUsageAnalyticsInDB, AIPromptTemplateCreate, AIPromptTemplateUpdate, AIPromptTemplateInDB,
    AudioRecordingRequest, TranscriptionRequest, AIAnalysisRequest, ClinicalSummaryResponse,
    DiagnosisSuggestion, ExamSuggestion, TreatmentSuggestion, ICDCodingSuggestion
)

logger = logging.getLogger(__name__)


class AudioBasedAIService:
    def __init__(self, db: Session):
        self.db = db
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.audio_storage_path = os.getenv("AUDIO_STORAGE_PATH", "/tmp/audio_recordings")
        self.openai_client = None
        self.whisper_model = None
        
        # Initialize storage directory
        os.makedirs(self.audio_storage_path, exist_ok=True)
        
        # Initialize AI models
        self._initialize_ai_models()

    def _encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()

    def _decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def _initialize_ai_models(self):
        """Initialize AI models and clients"""
        try:
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            
            # Initialize Whisper model (load on demand to save memory)
            logger.info("AI models initialization completed")
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")

    def _load_whisper_model(self, model_name: str = "base"):
        """Load Whisper model for transcription"""
        try:
            if not self.whisper_model or self.whisper_model.name != model_name:
                self.whisper_model = whisper.load_model(model_name)
                logger.info(f"Whisper model {model_name} loaded")
            return self.whisper_model
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            return None

    # Audio Recording Management
    def create_analysis_session(self, session_data: AIAnalysisSessionCreate, user_id: int) -> AIAnalysisSessionInDB:
        """Create a new AI analysis session"""
        try:
            session_id = f"ai_session_{uuid.uuid4().hex[:16]}"
            
            session_dict = session_data.dict()
            session_dict['session_id'] = session_id
            session_dict['doctor_id'] = user_id
            session_dict['status'] = AIAnalysisStatus.PENDING
            
            session = AIAnalysisSession(**session_dict)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            return AIAnalysisSessionInDB.from_orm(session)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating AI analysis session: {e}")
            raise

    def start_audio_recording(self, session_id: str, audio_data: bytes, audio_format: str = "webm") -> Dict[str, Any]:
        """Start audio recording for a session"""
        try:
            session = self.db.query(AIAnalysisSession).filter(
                AIAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if not session.recording_consent_given:
                return {"success": False, "error": "Recording consent not given"}
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{session_id}_{timestamp}.{audio_format}"
            file_path = os.path.join(self.audio_storage_path, filename)
            
            # Save audio file
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            # Update session with audio file info
            session.audio_file_path = file_path
            session.audio_format = audio_format
            session.status = AIAnalysisStatus.PROCESSING
            session.recording_started_at = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "success": True,
                "file_path": file_path,
                "session_id": session_id,
                "message": "Audio recording started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting audio recording: {e}")
            return {"success": False, "error": str(e)}

    def stop_audio_recording(self, session_id: str) -> Dict[str, Any]:
        """Stop audio recording and calculate duration"""
        try:
            session = self.db.query(AIAnalysisSession).filter(
                AIAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if not session.audio_file_path or not os.path.exists(session.audio_file_path):
                return {"success": False, "error": "No audio file found"}
            
            # Calculate duration (simplified - in production, use proper audio analysis)
            session.recording_ended_at = datetime.utcnow()
            if session.recording_started_at:
                duration = (session.recording_ended_at - session.recording_started_at).total_seconds()
                session.audio_duration_seconds = int(duration)
            
            session.status = AIAnalysisStatus.COMPLETED
            self.db.commit()
            
            return {
                "success": True,
                "duration_seconds": session.audio_duration_seconds,
                "file_size": os.path.getsize(session.audio_file_path),
                "message": "Audio recording stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"Error stopping audio recording: {e}")
            return {"success": False, "error": str(e)}

    # Transcription Services
    async def transcribe_audio(self, session_id: str, provider: AIProvider = AIProvider.OPENAI) -> Dict[str, Any]:
        """Transcribe audio using AI service"""
        try:
            session = self.db.query(AIAnalysisSession).filter(
                AIAnalysisSession.session_id == session_id
            ).first()
            
            if not session or not session.audio_file_path:
                return {"success": False, "error": "Session or audio file not found"}
            
            if not os.path.exists(session.audio_file_path):
                return {"success": False, "error": "Audio file does not exist"}
            
            transcription_result = None
            
            if provider == AIProvider.OPENAI and self.openai_client:
                transcription_result = await self._transcribe_with_openai(session)
            elif provider == AIProvider.LOCAL:
                transcription_result = await self._transcribe_with_whisper(session)
            else:
                return {"success": False, "error": f"Provider {provider} not supported"}
            
            if transcription_result["success"]:
                # Save transcription to database
                analysis = AIAnalysis(
                    session_id=session.id,
                    analysis_type=AIAnalysisType.TRANSCRIPTION,
                    input_data={"audio_file": session.audio_file_path},
                    output_data=transcription_result["data"],
                    confidence_score=transcription_result.get("confidence", 0.0),
                    processing_time_ms=transcription_result.get("processing_time", 0),
                    provider=provider.value,
                    model_used=transcription_result.get("model", ""),
                    status=AIAnalysisStatus.COMPLETED
                )
                self.db.add(analysis)
                self.db.commit()
                
                # Update session transcription info
                session.transcription_provider = provider
                session.transcription_confidence = transcription_result.get("confidence", 0.0)
                self.db.commit()
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {"success": False, "error": str(e)}

    async def _transcribe_with_openai(self, session: AIAnalysisSession) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            start_time = datetime.now()
            
            with open(session.audio_file_path, 'rb') as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=session.transcription_language,
                    response_format="verbose_json"
                )
            
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "text": transcript.text,
                "language": transcript.language,
                "duration": transcript.duration,
                "confidence": getattr(transcript, 'confidence', 0.95),
                "model": "whisper-1",
                "processing_time": processing_time,
                "segments": getattr(transcript, 'segments', [])
            }
            
        except Exception as e:
            logger.error(f"Error with OpenAI transcription: {e}")
            return {"success": False, "error": str(e)}

    async def _transcribe_with_whisper(self, session: AIAnalysisSession) -> Dict[str, Any]:
        """Transcribe audio using local Whisper model"""
        try:
            start_time = datetime.now()
            
            # Load Whisper model
            model = self._load_whisper_model(session.transcription_model)
            if not model:
                return {"success": False, "error": "Failed to load Whisper model"}
            
            # Transcribe audio
            result = model.transcribe(
                session.audio_file_path,
                language=session.transcription_language.split('-')[0] if session.transcription_language else None
            )
            
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "text": result["text"],
                "language": result.get("language", session.transcription_language),
                "confidence": 0.9,  # Whisper doesn't provide confidence scores
                "model": session.transcription_model,
                "processing_time": processing_time,
                "segments": result.get("segments", [])
            }
            
        except Exception as e:
            logger.error(f"Error with local Whisper transcription: {e}")
            return {"success": False, "error": str(e)}

    # AI Analysis Services
    async def analyze_transcription(self, session_id: str, analysis_type: AIAnalysisType) -> Dict[str, Any]:
        """Analyze transcription and generate medical insights"""
        try:
            session = self.db.query(AIAnalysisSession).filter(
                AIAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Get transcription
            transcription = self.db.query(AIAnalysis).filter(
                and_(
                    AIAnalysis.session_id == session.id,
                    AIAnalysis.analysis_type == AIAnalysisType.TRANSCRIPTION,
                    AIAnalysis.status == AIAnalysisStatus.COMPLETED
                )
            ).first()
            
            if not transcription:
                return {"success": False, "error": "No transcription found"}
            
            transcription_text = transcription.output_data.get("text", "")
            if not transcription_text:
                return {"success": False, "error": "Empty transcription"}
            
            # Perform analysis based on type
            analysis_result = None
            
            if analysis_type == AIAnalysisType.CLINICAL_SUMMARY:
                analysis_result = await self._generate_clinical_summary(transcription_text, session)
            elif analysis_type == AIAnalysisType.DIAGNOSIS_SUGGESTION:
                analysis_result = await self._generate_diagnosis_suggestions(transcription_text, session)
            elif analysis_type == AIAnalysisType.EXAM_SUGGESTION:
                analysis_result = await self._generate_exam_suggestions(transcription_text, session)
            elif analysis_type == AIAnalysisType.TREATMENT_SUGGESTION:
                analysis_result = await self._generate_treatment_suggestions(transcription_text, session)
            elif analysis_type == AIAnalysisType.ICD_CODING:
                analysis_result = await self._generate_icd_coding(transcription_text, session)
            else:
                return {"success": False, "error": f"Analysis type {analysis_type} not supported"}
            
            if analysis_result["success"]:
                # Save analysis to database
                analysis = AIAnalysis(
                    session_id=session.id,
                    analysis_type=analysis_type,
                    input_data={"transcription": transcription_text},
                    output_data=analysis_result["data"],
                    confidence_score=analysis_result.get("confidence", 0.0),
                    processing_time_ms=analysis_result.get("processing_time", 0),
                    provider=session.analysis_provider.value,
                    model_used=session.analysis_model,
                    status=AIAnalysisStatus.COMPLETED
                )
                self.db.add(analysis)
                self.db.commit()
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing transcription: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_clinical_summary(self, transcription: str, session: AIAnalysisSession) -> Dict[str, Any]:
        """Generate structured clinical summary"""
        try:
            start_time = datetime.now()
            
            prompt = f"""
            Como um assistente médico especializado, analise a seguinte transcrição de consulta médica e gere um resumo clínico estruturado em português brasileiro.

            Transcrição:
            {transcription}

            Por favor, organize o resumo nas seguintes seções:
            1. Queixa Principal
            2. História da Doença Atual
            3. Antecedentes Médicos Relevantes
            4. Exame Físico (se mencionado)
            5. Hipóteses Diagnósticas
            6. Plano Terapêutico
            7. Orientações ao Paciente

            Responda em formato JSON estruturado.
            """
            
            if session.analysis_provider == AIProvider.OPENAI and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=session.analysis_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=session.analysis_temperature,
                    max_tokens=session.analysis_max_tokens
                )
                
                content = response.choices[0].message.content
            else:
                # Fallback to simple text processing
                content = self._simple_clinical_summary(transcription)
            
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "data": {
                    "summary": content,
                    "structured_data": self._parse_clinical_summary(content),
                    "word_count": len(transcription.split()),
                    "summary_length": len(content)
                },
                "confidence": 0.85,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating clinical summary: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_diagnosis_suggestions(self, transcription: str, session: AIAnalysisSession) -> Dict[str, Any]:
        """Generate diagnosis suggestions with ICD-10 codes"""
        try:
            start_time = datetime.now()
            
            prompt = f"""
            Como um médico especialista, analise a seguinte transcrição de consulta e sugira possíveis diagnósticos com códigos CID-10.

            Transcrição:
            {transcription}

            Para cada diagnóstico sugerido, forneça:
            1. Código CID-10
            2. Descrição do diagnóstico
            3. Probabilidade (alta, média, baixa)
            4. Justificativa baseada nos sintomas mencionados

            Responda em formato JSON.
            """
            
            if session.analysis_provider == AIProvider.OPENAI and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=session.analysis_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=session.analysis_temperature,
                    max_tokens=session.analysis_max_tokens
                )
                
                content = response.choices[0].message.content
            else:
                content = self._simple_diagnosis_suggestions(transcription)
            
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "data": {
                    "diagnoses": self._parse_diagnosis_suggestions(content),
                    "total_suggestions": len(self._parse_diagnosis_suggestions(content))
                },
                "confidence": 0.80,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating diagnosis suggestions: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_exam_suggestions(self, transcription: str, session: AIAnalysisSession) -> Dict[str, Any]:
        """Generate exam suggestions based on consultation"""
        try:
            start_time = datetime.now()
            
            prompt = f"""
            Como um médico especialista, analise a seguinte transcrição de consulta e sugira exames complementares apropriados.

            Transcrição:
            {transcription}

            Para cada exame sugerido, forneça:
            1. Nome do exame
            2. Tipo (laboratorial, imagem, funcional, etc.)
            3. Urgência (urgente, rotina, acompanhamento)
            4. Justificativa clínica

            Responda em formato JSON.
            """
            
            if session.analysis_provider == AIProvider.OPENAI and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=session.analysis_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=session.analysis_temperature,
                    max_tokens=session.analysis_max_tokens
                )
                
                content = response.choices[0].message.content
            else:
                content = self._simple_exam_suggestions(transcription)
            
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "data": {
                    "exams": self._parse_exam_suggestions(content),
                    "total_suggestions": len(self._parse_exam_suggestions(content))
                },
                "confidence": 0.75,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating exam suggestions: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_treatment_suggestions(self, transcription: str, session: AIAnalysisSession) -> Dict[str, Any]:
        """Generate treatment suggestions"""
        try:
            start_time = datetime.now()
            
            prompt = f"""
            Como um médico especialista, analise a seguinte transcrição de consulta e sugira tratamentos apropriados.

            Transcrição:
            {transcription}

            Para cada tratamento sugerido, forneça:
            1. Tipo de tratamento (medicamentoso, cirúrgico, fisioterápico, etc.)
            2. Descrição específica
            3. Duração estimada
            4. Considerações especiais

            Responda em formato JSON.
            """
            
            if session.analysis_provider == AIProvider.OPENAI and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=session.analysis_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=session.analysis_temperature,
                    max_tokens=session.analysis_max_tokens
                )
                
                content = response.choices[0].message.content
            else:
                content = self._simple_treatment_suggestions(transcription)
            
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "data": {
                    "treatments": self._parse_treatment_suggestions(content),
                    "total_suggestions": len(self._parse_treatment_suggestions(content))
                },
                "confidence": 0.75,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating treatment suggestions: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_icd_coding(self, transcription: str, session: AIAnalysisSession) -> Dict[str, Any]:
        """Generate ICD-10 coding suggestions"""
        try:
            start_time = datetime.now()
            
            prompt = f"""
            Como um especialista em codificação médica, analise a seguinte transcrição de consulta e sugira códigos CID-10 apropriados.

            Transcrição:
            {transcription}

            Para cada código sugerido, forneça:
            1. Código CID-10
            2. Descrição oficial
            3. Tipo (principal, secundário, comorbidade)
            4. Confiabilidade da codificação

            Responda em formato JSON.
            """
            
            if session.analysis_provider == AIProvider.OPENAI and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=session.analysis_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,  # Lower temperature for more consistent coding
                    max_tokens=session.analysis_max_tokens
                )
                
                content = response.choices[0].message.content
            else:
                content = self._simple_icd_coding(transcription)
            
            end_time = datetime.now()
            processing_time = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                "success": True,
                "data": {
                    "codes": self._parse_icd_coding(content),
                    "total_codes": len(self._parse_icd_coding(content))
                },
                "confidence": 0.70,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating ICD coding: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods for parsing AI responses
    def _parse_clinical_summary(self, content: str) -> Dict[str, str]:
        """Parse clinical summary into structured format"""
        try:
            # Try to parse as JSON first
            if content.strip().startswith('{'):
                return json.loads(content)
            
            # Fallback to text parsing
            sections = {
                "queixa_principal": "",
                "historia_doenca_atual": "",
                "antecedentes_medicos": "",
                "exame_fisico": "",
                "hipoteses_diagnosticas": "",
                "plano_terapeutico": "",
                "orientacoes_paciente": ""
            }
            
            # Simple text parsing logic here
            return sections
        except Exception as e:
            logger.error(f"Error parsing clinical summary: {e}")
            return {}

    def _parse_diagnosis_suggestions(self, content: str) -> List[Dict[str, Any]]:
        """Parse diagnosis suggestions"""
        try:
            if content.strip().startswith('['):
                return json.loads(content)
            return []
        except Exception as e:
            logger.error(f"Error parsing diagnosis suggestions: {e}")
            return []

    def _parse_exam_suggestions(self, content: str) -> List[Dict[str, Any]]:
        """Parse exam suggestions"""
        try:
            if content.strip().startswith('['):
                return json.loads(content)
            return []
        except Exception as e:
            logger.error(f"Error parsing exam suggestions: {e}")
            return []

    def _parse_treatment_suggestions(self, content: str) -> List[Dict[str, Any]]:
        """Parse treatment suggestions"""
        try:
            if content.strip().startswith('['):
                return json.loads(content)
            return []
        except Exception as e:
            logger.error(f"Error parsing treatment suggestions: {e}")
            return []

    def _parse_icd_coding(self, content: str) -> List[Dict[str, Any]]:
        """Parse ICD coding suggestions"""
        try:
            if content.strip().startswith('['):
                return json.loads(content)
            return []
        except Exception as e:
            logger.error(f"Error parsing ICD coding: {e}")
            return []

    # Fallback methods for when AI services are not available
    def _simple_clinical_summary(self, transcription: str) -> str:
        """Generate simple clinical summary without AI"""
        return f"Resumo clínico baseado na consulta:\n\n{transcription[:500]}..."

    def _simple_diagnosis_suggestions(self, transcription: str) -> str:
        """Generate simple diagnosis suggestions"""
        return '[{"codigo": "Z00.0", "descricao": "Exame médico geral", "probabilidade": "baixa", "justificativa": "Consulta de rotina"}]'

    def _simple_exam_suggestions(self, transcription: str) -> str:
        """Generate simple exam suggestions"""
        return '[{"nome": "Hemograma completo", "tipo": "laboratorial", "urgencia": "rotina", "justificativa": "Exame de rotina"}]'

    def _simple_treatment_suggestions(self, transcription: str) -> str:
        """Generate simple treatment suggestions"""
        return '[{"tipo": "medicamentoso", "descricao": "Medicação conforme prescrição médica", "duracao": "conforme orientação", "consideracoes": "Seguir orientações médicas"}]'

    def _simple_icd_coding(self, transcription: str) -> str:
        """Generate simple ICD coding"""
        return '[{"codigo": "Z00.0", "descricao": "Exame médico geral", "tipo": "principal", "confiabilidade": "baixa"}]'

    # Session Management
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for an AI analysis session"""
        try:
            session = self.db.query(AIAnalysisSession).filter(
                AIAnalysisSession.session_id == session_id
            ).first()
            
            if not session:
                return {"error": "Session not found"}
            
            # Get all analyses for this session
            analyses = self.db.query(AIAnalysis).filter(
                AIAnalysis.session_id == session.id
            ).all()
            
            analytics = {
                "session_id": session_id,
                "total_analyses": len(analyses),
                "audio_duration": session.audio_duration_seconds,
                "transcription_confidence": session.transcription_confidence,
                "analyses_by_type": {},
                "total_processing_time": 0,
                "success_rate": 0
            }
            
            successful_analyses = 0
            for analysis in analyses:
                analysis_type = analysis.analysis_type.value
                if analysis_type not in analytics["analyses_by_type"]:
                    analytics["analyses_by_type"][analysis_type] = 0
                analytics["analyses_by_type"][analysis_type] += 1
                
                analytics["total_processing_time"] += analysis.processing_time_ms or 0
                
                if analysis.status == AIAnalysisStatus.COMPLETED:
                    successful_analyses += 1
            
            analytics["success_rate"] = (successful_analyses / len(analyses)) * 100 if analyses else 0
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            return {"error": str(e)}

    # Configuration Management
    def get_configuration(self) -> AIConfigurationInDB:
        """Get AI configuration"""
        config = self.db.query(AIConfiguration).first()
        if not config:
            # Create default configuration
            config = AIConfiguration(
                default_provider=AIProvider.OPENAI.value,
                openai_api_key="",  # Will be set by admin
                anthropic_api_key="",
                google_api_key="",
                azure_endpoint="",
                azure_api_key="",
                default_transcription_model="whisper-1",
                default_analysis_model="gpt-4",
                max_audio_duration_minutes=60,
                auto_transcribe=True,
                auto_analyze=True,
                retention_days=30,
                encryption_enabled=True
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
        
        return AIConfigurationInDB.from_orm(config)

    def update_configuration(self, config_data: AIConfigurationUpdate) -> AIConfigurationInDB:
        """Update AI configuration"""
        config = self.db.query(AIConfiguration).first()
        if not config:
            config = AIConfiguration(**config_data.dict())
            self.db.add(config)
        else:
            update_data = config_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(config, field, value)
        
        self.db.commit()
        self.db.refresh(config)
        return AIConfigurationInDB.from_orm(config)
