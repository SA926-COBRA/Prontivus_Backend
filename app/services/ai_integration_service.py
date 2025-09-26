import os
import json
import logging
import asyncio
import uuid
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_, desc
from decimal import Decimal
import time

from app.models.ai_integration import (
    AIConfiguration, AIProcessingJob, PreConsultationSummary,
    MedicalTranscription, ClinicalNotes, AIUsageLog, AIModel, AIFeedback
)
from app.schemas.ai_integration import (
    AIProcessingRequest, PreConsultationSummaryRequest,
    MedicalTranscriptionRequest, ClinicalNotesRequest,
    AIUsageSearchRequest, AISummary, AIAnalytics
)

logger = logging.getLogger(__name__)

class AIIntegrationService:
    """Service for AI Integration and processing"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # AI Configuration Management
    def create_ai_configuration(self, configuration_data: dict, user_id: int) -> AIConfiguration:
        """Create a new AI configuration"""
        try:
            configuration = AIConfiguration(
                **configuration_data,
                created_by=user_id
            )
            
            self.db.add(configuration)
            self.db.commit()
            self.db.refresh(configuration)
            
            return configuration
        except Exception as e:
            logger.error(f"Error creating AI configuration: {e}")
            raise
    
    def get_ai_configuration(self, configuration_id: int) -> Optional[AIConfiguration]:
        """Get AI configuration by ID"""
        return self.db.query(AIConfiguration).filter(
            AIConfiguration.id == configuration_id
        ).first()
    
    def get_active_configurations(self, task_type: str = None) -> List[AIConfiguration]:
        """Get active AI configurations"""
        query = self.db.query(AIConfiguration).filter(AIConfiguration.is_active == True)
        
        if task_type:
            query = query.filter(AIConfiguration.task_type == task_type)
        
        return query.all()
    
    # AI Processing Job Management
    def create_processing_job(self, request: AIProcessingRequest, user_id: int) -> AIProcessingJob:
        """Create a new AI processing job"""
        try:
            # Generate job ID
            job_id = self._generate_job_id()
            
            # Create processing job
            job = AIProcessingJob(
                job_id=job_id,
                configuration_id=request.configuration_id,
                task_type=request.task_type,
                input_data=request.input_data,
                input_text=request.input_text,
                input_metadata=request.input_metadata,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                appointment_id=request.appointment_id,
                created_by=user_id
            )
            
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            return job
        except Exception as e:
            logger.error(f"Error creating processing job: {e}")
            raise
    
    def process_ai_request(self, request: AIProcessingRequest, user_id: int) -> AIProcessingJob:
        """Process AI request and return results"""
        try:
            # Create processing job
            job = self.create_processing_job(request, user_id)
            
            # Get configuration
            configuration = self.get_ai_configuration(request.configuration_id)
            if not configuration:
                raise ValueError("AI configuration not found")
            
            # Update job status
            job.status = "processing"
            job.started_at = datetime.utcnow()
            self.db.commit()
            
            # Process with AI
            try:
                result = self._process_with_ai(configuration, request)
                
                # Update job with results
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.processing_time_seconds = (job.completed_at - job.started_at).total_seconds()
                job.output_data = result.get('output_data')
                job.output_text = result.get('output_text')
                job.confidence_score = result.get('confidence_score')
                job.tokens_used = result.get('tokens_used')
                job.cost = result.get('cost')
                
                # Update configuration statistics
                configuration.last_used = datetime.utcnow()
                configuration.usage_count += 1
                configuration.success_count += 1
                if configuration.average_response_time:
                    configuration.average_response_time = (
                        configuration.average_response_time + job.processing_time_seconds
                    ) / 2
                else:
                    configuration.average_response_time = job.processing_time_seconds
                
                if job.cost:
                    configuration.total_cost += job.cost
                
            except Exception as e:
                # Update job with error
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                job.processing_time_seconds = (job.completed_at - job.started_at).total_seconds()
                job.error_message = str(e)
                
                # Update configuration statistics
                configuration.failure_count += 1
                
                logger.error(f"Error processing AI request: {e}")
            
            self.db.commit()
            self.db.refresh(job)
            
            return job
        except Exception as e:
            logger.error(f"Error processing AI request: {e}")
            raise
    
    # Pre-Consultation Summary
    def generate_pre_consultation_summary(self, request: PreConsultationSummaryRequest, user_id: int) -> PreConsultationSummary:
        """Generate pre-consultation summary using AI"""
        try:
            # Get configuration for pre-consultation summary
            configuration = self.get_active_configurations("pre_consultation_summary")
            if not configuration:
                raise ValueError("No active AI configuration for pre-consultation summary")
            
            configuration = configuration[0]  # Use first active configuration
            
            # Prepare input data
            input_data = {
                "patient_data": request.patient_data,
                "medical_history": request.medical_history,
                "current_symptoms": request.current_symptoms
            }
            
            # Create processing request
            processing_request = AIProcessingRequest(
                configuration_id=configuration.id,
                task_type="pre_consultation_summary",
                input_data=input_data,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                appointment_id=request.appointment_id
            )
            
            # Process with AI
            job = self.process_ai_request(processing_request, user_id)
            
            # Generate summary ID
            summary_id = self._generate_summary_id()
            
            # Create pre-consultation summary
            summary = PreConsultationSummary(
                summary_id=summary_id,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                appointment_id=request.appointment_id,
                processing_job_id=job.id,
                confidence_score=job.confidence_score,
                created_by=user_id
            )
            
            # Parse AI output and populate summary fields
            if job.output_data:
                summary.chief_complaint = job.output_data.get('chief_complaint')
                summary.history_of_present_illness = job.output_data.get('history_of_present_illness')
                summary.past_medical_history = job.output_data.get('past_medical_history')
                summary.medications = job.output_data.get('medications')
                summary.allergies = job.output_data.get('allergies')
                summary.social_history = job.output_data.get('social_history')
                summary.family_history = job.output_data.get('family_history')
                summary.review_of_systems = job.output_data.get('review_of_systems')
                summary.risk_factors = job.output_data.get('risk_factors')
                summary.potential_diagnoses = job.output_data.get('potential_diagnoses')
                summary.recommended_tests = job.output_data.get('recommended_tests')
                summary.clinical_notes = job.output_data.get('clinical_notes')
            
            self.db.add(summary)
            self.db.commit()
            self.db.refresh(summary)
            
            return summary
        except Exception as e:
            logger.error(f"Error generating pre-consultation summary: {e}")
            raise
    
    # Medical Transcription
    def process_medical_transcription(self, request: MedicalTranscriptionRequest, user_id: int) -> MedicalTranscription:
        """Process medical transcription using AI"""
        try:
            # Get configuration for medical transcription
            configuration = self.get_active_configurations("medical_transcription")
            if not configuration:
                raise ValueError("No active AI configuration for medical transcription")
            
            configuration = configuration[0]  # Use first active configuration
            
            # Prepare input data
            input_data = {
                "audio_file_path": request.audio_file_path,
                "audio_metadata": request.audio_metadata
            }
            
            # Create processing request
            processing_request = AIProcessingRequest(
                configuration_id=configuration.id,
                task_type="medical_transcription",
                input_data=input_data,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                appointment_id=request.appointment_id
            )
            
            # Process with AI
            job = self.process_ai_request(processing_request, user_id)
            
            # Generate transcription ID
            transcription_id = self._generate_transcription_id()
            
            # Create medical transcription
            transcription = MedicalTranscription(
                transcription_id=transcription_id,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                appointment_id=request.appointment_id,
                processing_job_id=job.id,
                audio_file_path=request.audio_file_path,
                confidence_score=job.confidence_score,
                created_by=user_id
            )
            
            # Parse AI output and populate transcription fields
            if job.output_data:
                transcription.raw_transcription = job.output_data.get('raw_transcription')
                transcription.cleaned_transcription = job.output_data.get('cleaned_transcription')
                transcription.structured_transcription = job.output_data.get('structured_transcription')
                transcription.speaker_identification = job.output_data.get('speaker_identification')
                transcription.medical_terms = job.output_data.get('medical_terms')
                transcription.key_phrases = job.output_data.get('key_phrases')
                transcription.sentiment_analysis = job.output_data.get('sentiment_analysis')
                transcription.audio_duration_seconds = job.output_data.get('audio_duration_seconds')
                transcription.audio_quality = job.output_data.get('audio_quality')
            
            self.db.add(transcription)
            self.db.commit()
            self.db.refresh(transcription)
            
            return transcription
        except Exception as e:
            logger.error(f"Error processing medical transcription: {e}")
            raise
    
    # Clinical Notes
    def generate_clinical_notes(self, request: ClinicalNotesRequest, user_id: int) -> ClinicalNotes:
        """Generate clinical notes using AI"""
        try:
            # Get configuration for clinical notes
            configuration = self.get_active_configurations("clinical_notes")
            if not configuration:
                raise ValueError("No active AI configuration for clinical notes")
            
            configuration = configuration[0]  # Use first active configuration
            
            # Prepare input data
            input_data = {
                "consultation_data": request.consultation_data,
                "patient_interview": request.patient_interview
            }
            
            # Create processing request
            processing_request = AIProcessingRequest(
                configuration_id=configuration.id,
                task_type="clinical_notes",
                input_data=input_data,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                appointment_id=request.appointment_id
            )
            
            # Process with AI
            job = self.process_ai_request(processing_request, user_id)
            
            # Generate notes ID
            notes_id = self._generate_notes_id()
            
            # Create clinical notes
            notes = ClinicalNotes(
                notes_id=notes_id,
                patient_id=request.patient_id,
                doctor_id=request.doctor_id,
                appointment_id=request.appointment_id,
                processing_job_id=job.id,
                confidence_score=job.confidence_score,
                created_by=user_id
            )
            
            # Parse AI output and populate notes fields
            if job.output_data:
                notes.subjective = job.output_data.get('subjective')
                notes.objective = job.output_data.get('objective')
                notes.assessment = job.output_data.get('assessment')
                notes.plan = job.output_data.get('plan')
                notes.diagnosis_suggestions = job.output_data.get('diagnosis_suggestions')
                notes.treatment_recommendations = job.output_data.get('treatment_recommendations')
                notes.follow_up_notes = job.output_data.get('follow_up_notes')
                notes.risk_assessment = job.output_data.get('risk_assessment')
            
            self.db.add(notes)
            self.db.commit()
            self.db.refresh(notes)
            
            return notes
        except Exception as e:
            logger.error(f"Error generating clinical notes: {e}")
            raise
    
    # Usage and Analytics
    def get_ai_usage_logs(self, request: AIUsageSearchRequest) -> List[AIUsageLog]:
        """Get AI usage logs with filtering"""
        try:
            query = self.db.query(AIUsageLog)
            
            if request.configuration_id:
                query = query.filter(AIUsageLog.configuration_id == request.configuration_id)
            
            if request.user_id:
                query = query.filter(AIUsageLog.user_id == request.user_id)
            
            if request.task_type:
                query = query.filter(AIUsageLog.task_type == request.task_type)
            
            if request.date_from:
                query = query.filter(AIUsageLog.request_timestamp >= request.date_from)
            
            if request.date_to:
                query = query.filter(AIUsageLog.request_timestamp <= request.date_to)
            
            logs = query.order_by(desc(AIUsageLog.request_timestamp)).offset(
                request.skip
            ).limit(request.limit).all()
            
            return logs
        except Exception as e:
            logger.error(f"Error getting AI usage logs: {e}")
            raise
    
    def get_ai_summary(self) -> AISummary:
        """Get AI usage summary statistics"""
        try:
            # Configuration statistics
            total_configurations = self.db.query(AIConfiguration).count()
            active_configurations = self.db.query(AIConfiguration).filter(
                AIConfiguration.is_active == True
            ).count()
            
            # Processing job statistics
            total_processing_jobs = self.db.query(AIProcessingJob).count()
            completed_jobs = self.db.query(AIProcessingJob).filter(
                AIProcessingJob.status == "completed"
            ).count()
            failed_jobs = self.db.query(AIProcessingJob).filter(
                AIProcessingJob.status == "failed"
            ).count()
            
            # Usage statistics
            total_usage = self.db.query(AIUsageLog).count()
            
            # Cost statistics
            total_cost = self.db.query(AIUsageLog).with_entities(
                func.sum(AIUsageLog.cost)
            ).scalar() or Decimal('0')
            
            # Performance statistics
            avg_response_time = self.db.query(AIUsageLog).with_entities(
                func.avg(AIUsageLog.response_time_ms)
            ).filter(AIUsageLog.response_time_ms.isnot(None)).scalar() or 0
            
            # Success rate
            successful_requests = self.db.query(AIUsageLog).filter(
                AIUsageLog.success == True
            ).count()
            success_rate = (successful_requests / total_usage * 100) if total_usage > 0 else 0
            
            return AISummary(
                total_configurations=total_configurations,
                active_configurations=active_configurations,
                total_processing_jobs=total_processing_jobs,
                completed_jobs=completed_jobs,
                failed_jobs=failed_jobs,
                total_usage=total_usage,
                total_cost=total_cost,
                average_response_time=avg_response_time,
                success_rate=success_rate
            )
        except Exception as e:
            logger.error(f"Error getting AI summary: {e}")
            raise
    
    def get_ai_analytics(self) -> AIAnalytics:
        """Get detailed AI analytics"""
        try:
            # Basic statistics
            total_configurations = self.db.query(AIConfiguration).count()
            active_configurations = self.db.query(AIConfiguration).filter(
                AIConfiguration.is_active == True
            ).count()
            
            # Configurations by provider
            provider_stats = self.db.query(
                AIConfiguration.provider,
                func.count(AIConfiguration.id)
            ).group_by(AIConfiguration.provider).all()
            
            configurations_by_provider = {
                stat[0].value: stat[1] for stat in provider_stats
            }
            
            # Configurations by task type
            task_type_stats = self.db.query(
                AIConfiguration.task_type,
                func.count(AIConfiguration.id)
            ).group_by(AIConfiguration.task_type).all()
            
            configurations_by_task_type = {
                stat[0].value: stat[1] for stat in task_type_stats
            }
            
            # Processing job statistics
            job_stats = self.db.query(
                AIProcessingJob.status,
                func.count(AIProcessingJob.id)
            ).group_by(AIProcessingJob.status).all()
            
            processing_job_statistics = {
                stat[0].value: stat[1] for stat in job_stats
            }
            
            # Usage statistics
            usage_stats = self.db.query(
                AIUsageLog.task_type,
                func.count(AIUsageLog.id)
            ).group_by(AIUsageLog.task_type).all()
            
            usage_statistics = {
                stat[0].value: stat[1] for stat in usage_stats
            }
            
            # Cost statistics
            cost_stats = self.db.query(
                AIUsageLog.task_type,
                func.sum(AIUsageLog.cost)
            ).group_by(AIUsageLog.task_type).all()
            
            cost_statistics = {
                stat[0].value: stat[1] or Decimal('0') for stat in cost_stats
            }
            
            # Performance metrics
            avg_response_time = self.db.query(AIUsageLog).with_entities(
                func.avg(AIUsageLog.response_time_ms)
            ).filter(AIUsageLog.response_time_ms.isnot(None)).scalar() or 0
            
            success_rate = self.db.query(AIUsageLog).filter(
                AIUsageLog.success == True
            ).count() / self.db.query(AIUsageLog).count() * 100 if self.db.query(AIUsageLog).count() > 0 else 0
            
            performance_metrics = {
                "average_response_time_ms": avg_response_time,
                "success_rate": success_rate
            }
            
            # Model performance
            model_performance = {}
            configurations = self.db.query(AIConfiguration).all()
            for config in configurations:
                if config.average_response_time:
                    model_performance[config.model_name] = config.average_response_time
            
            # User feedback
            user_feedback = {}
            feedback_stats = self.db.query(
                AIFeedback.feedback_type,
                func.avg(AIFeedback.rating)
            ).group_by(AIFeedback.feedback_type).all()
            
            for stat in feedback_stats:
                user_feedback[stat[0]] = float(stat[1]) if stat[1] else 0
            
            return AIAnalytics(
                total_configurations=total_configurations,
                active_configurations=active_configurations,
                configurations_by_provider=configurations_by_provider,
                configurations_by_task_type=configurations_by_task_type,
                processing_job_statistics=processing_job_statistics,
                usage_statistics=usage_statistics,
                cost_statistics=cost_statistics,
                performance_metrics=performance_metrics,
                model_performance=model_performance,
                user_feedback=user_feedback
            )
        except Exception as e:
            logger.error(f"Error getting AI analytics: {e}")
            raise
    
    # Private helper methods
    def _process_with_ai(self, configuration: AIConfiguration, request: AIProcessingRequest) -> Dict[str, Any]:
        """Process request with AI provider"""
        try:
            # Mock AI processing
            # In real implementation, this would call the actual AI provider API
            
            start_time = time.time()
            
            # Simulate AI processing
            if configuration.provider.value == "openai":
                result = self._process_with_openai(configuration, request)
            elif configuration.provider.value == "anthropic":
                result = self._process_with_anthropic(configuration, request)
            else:
                result = self._process_with_generic(configuration, request)
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log usage
            self._log_ai_usage(configuration, request, result, processing_time)
            
            return result
        except Exception as e:
            logger.error(f"Error processing with AI: {e}")
            raise
    
    def _process_with_openai(self, configuration: AIConfiguration, request: AIProcessingRequest) -> Dict[str, Any]:
        """Process with OpenAI API"""
        # Mock OpenAI processing
        return {
            "output_data": {
                "summary": "AI-generated summary based on patient data",
                "confidence": 0.85
            },
            "output_text": "AI-generated text response",
            "confidence_score": 0.85,
            "tokens_used": 150,
            "cost": Decimal('0.003')
        }
    
    def _process_with_anthropic(self, configuration: AIConfiguration, request: AIProcessingRequest) -> Dict[str, Any]:
        """Process with Anthropic API"""
        # Mock Anthropic processing
        return {
            "output_data": {
                "summary": "AI-generated summary based on patient data",
                "confidence": 0.90
            },
            "output_text": "AI-generated text response",
            "confidence_score": 0.90,
            "tokens_used": 200,
            "cost": Decimal('0.004')
        }
    
    def _process_with_generic(self, configuration: AIConfiguration, request: AIProcessingRequest) -> Dict[str, Any]:
        """Process with generic AI provider"""
        # Mock generic processing
        return {
            "output_data": {
                "summary": "AI-generated summary based on patient data",
                "confidence": 0.80
            },
            "output_text": "AI-generated text response",
            "confidence_score": 0.80,
            "tokens_used": 100,
            "cost": Decimal('0.002')
        }
    
    def _log_ai_usage(self, configuration: AIConfiguration, request: AIProcessingRequest, result: Dict[str, Any], processing_time: float):
        """Log AI usage for analytics"""
        try:
            usage_log = AIUsageLog(
                configuration_id=configuration.id,
                task_type=request.task_type,
                input_tokens=result.get('tokens_used', 0),
                output_tokens=result.get('tokens_used', 0),
                total_tokens=result.get('tokens_used', 0),
                response_time_ms=int(processing_time),
                success=True,
                cost=result.get('cost'),
                cost_per_token=configuration.cost_per_token,
                metadata={
                    "model_name": configuration.model_name,
                    "provider": configuration.provider.value
                }
            )
            
            self.db.add(usage_log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging AI usage: {e}")
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"AI{timestamp}{random_part}"
    
    def _generate_summary_id(self) -> str:
        """Generate unique summary ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"SUM{timestamp}{random_part}"
    
    def _generate_transcription_id(self) -> str:
        """Generate unique transcription ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"TRN{timestamp}{random_part}"
    
    def _generate_notes_id(self) -> str:
        """Generate unique notes ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid.uuid4())[:8].upper()
        return f"NOT{timestamp}{random_part}"
