"""
Summarization Service

Generates summaries from text using Ollama (local LLM).
"""
import os
import requests
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SummarizationService:
    """Service for generating summaries using Ollama"""
    
    def __init__(self, ollama_url: str = None, model_name: str = "llama3.2:13b"):
        """
        Initialize summarization service
        
        Args:
            ollama_url: URL of Ollama service (default: from env or http://ollama:11434)
            model_name: Model to use for summarization
        """
        self.ollama_url = ollama_url or os.environ.get("OLLAMA_URL", "http://ollama:11434")
        # Allow overriding via env var so we can switch models without code edits
        self.model_name = os.environ.get("OLLAMA_MODEL", model_name)
        self.max_transcript_length = 50000  # ~50k characters max
        self.timeout = 2700  # 45 minutes timeout
    
    def summarize_transcript(self, transcript: str, model_name: str = None) -> Dict[str, any]:
        """
        Generate summary from transcript text using Ollama
        
        Args:
            transcript: The transcript text to summarize
            model_name: Override the default model for this request
            
        Returns:
            Dict with success status, summary text, and any errors
        """
        try:
            # Validate input
            if not transcript or not transcript.strip():
                return {
                    'success': False,
                    'summary': None,
                    'error': 'Empty transcript provided'
                }
            
            transcript = transcript.strip()
            
            # Check transcript length
            if len(transcript) > self.max_transcript_length:
                return {
                    'success': False,
                    'summary': None,
                    'error': f'Transcript too long: {len(transcript)} characters (max {self.max_transcript_length})'
                }
            
            # Use provided model or default
            model = model_name or self.model_name
            
            # Check if Ollama is available
            health_check = self.check_ollama_health()
            if not health_check['healthy']:
                return {
                    'success': False,
                    'summary': None,
                    'error': f'Ollama service unavailable: {health_check["error"]}'
                }
            
            # Create summarization prompt
            prompt = self._create_summary_prompt(transcript)
            
            logger.info(f"Generating summary using {model} for {len(transcript)} characters")
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "top_p": 0.9,
                        "max_tokens": 3500,  # More detailed summaries for 13B
                        "stop": ["</summary>", "\n\n---"]
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'summary': None,
                    'error': error_msg
                }
            
            result = response.json()
            summary_text = result.get('response', '').strip()
            
            if not summary_text:
                return {
                    'success': False,
                    'summary': None,
                    'error': 'Model returned empty summary'
                }
            
            # Post-process the summary
            processed_summary = self._post_process_summary(summary_text)
            
            logger.info(f"Successfully generated summary: {len(processed_summary)} characters")
            
            return {
                'success': True,
                'summary': processed_summary,
                'model_used': model,
                'tokens_used': result.get('eval_count', 0),
                'processing_time': result.get('total_duration', 0) / 1000000000,  # Convert to seconds
                'error': None
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Summarization timeout after {self.timeout}s")
            return {
                'success': False,
                'summary': None,
                'error': f'Summarization timeout after {self.timeout} seconds'
            }
        except requests.exceptions.ConnectionError:
            logger.error("Connection to Ollama service failed")
            return {
                'success': False,
                'summary': None,
                'error': 'Connection to Ollama service failed'
            }
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return {
                'success': False,
                'summary': None,
                'error': f'Summarization failed: {str(e)}'
            }
    
    def _create_summary_prompt(self, transcript: str) -> str:
        """Create an effective prompt for comprehensive summarization"""
        # Increase transcript size for more detailed summaries
        max_chars = 15000  # Increased from 8000 for more detail
        if len(transcript) > max_chars:
            # Take first part and last part to capture intro and conclusion
            first_part = transcript[:max_chars//2]
            last_part = transcript[-(max_chars//2):]
            limited_transcript = f"{first_part}\n\n[... content truncated ...]\n\n{last_part}"
        else:
            limited_transcript = transcript
            
        return f"""You are a world‑class technical explainer. Read the transcript and produce a rich, structured, highly useful summary. Do not add any preface like “here is the summary”. Start with the sections below. Use short, information‑dense bullets.

RESPONSE FORMAT (strict):

**KEY POINTS:**
• 3–6 bullets with the core takeaways and learning objectives
• Include at least one practical outcome the viewer can do after watching

**DETAILED SUMMARY:**
• Expand the topic with concrete details and miniature examples
• Explain important concepts and decisions, not just list them
• If a process is described, include a short numbered mini‑guide:
  1) step … 2) step … 3) step …
• Call out caveats/pitfalls where relevant

*KEY CONCEPTS, METHODOLOGIES, AND TECHNICAL DETAILS:**
• Key terms with one‑line explanations (term — meaning)

*TOOLS, FRAMEWORKS, OR TECHNOLOGIES REFERENCED:**
• Name — what it was used for in this context

*PREREQUISITES OR BACKGROUND KNOWLEDGE DISCUSSED:**
• What the viewer should know beforehand

*PRACTICAL APPLICATIONS AND REAL‑WORLD USE CASES:**
• Where and how to apply this

*STEP‑BY‑STEP PROCESSES OR WORKFLOWS MENTIONED:**
• If any, summarize as concise numbered steps

Rules:
- Keep bullets succinct; avoid narrative filler.
- Do not echo the instructions or say “the transcript says”.
- Use only ASCII bullets (•) and numbered lists as shown.

Transcript:
{limited_transcript}

**KEY POINTS:**
•"""
    
    def _post_process_summary(self, raw_summary: str) -> str:
        """Clean and format the generated summary"""
        import re
        
        # Remove common artifacts
        summary = raw_summary.strip()
        
        # Remove prompt echoes
        for prefix in ["Summary:", "Key Points:", "Here is", "Here are", "This video", "The video"]:
            if summary.startswith(prefix):
                summary = summary[len(prefix):].strip()
        
        # Remove specific unwanted phrases
        unwanted_phrases = [
            r'the summary of the transcript in the requested format:?\s*',
            r'here is the summary of the transcript:?\s*',
            r'here\'s the summary:?\s*',
            r'summary of the transcript:?\s*',
            r'here is a comprehensive summary:?\s*',
            r'here\'s a comprehensive summary:?\s*',
            r'based on the transcript:?\s*',
            r'transcript summary:?\s*'
        ]
        
        for phrase in unwanted_phrases:
            summary = re.sub(phrase, '', summary, flags=re.IGNORECASE)
        
        # Remove introductory phrases at the start
        summary = re.sub(r'^(Here is|Here are|This is|The following|Below are).*?:', '', summary, flags=re.IGNORECASE).strip()
        
        # Ensure bullet points are properly formatted
        # Convert various bullet formats to consistent bullets
        summary = re.sub(r'^[-*]\s*', '• ', summary, flags=re.MULTILINE)
        summary = re.sub(r'^\d+\.\s*', '• ', summary, flags=re.MULTILINE)
        
        # If no bullets exist, try to create them from sentences/paragraphs
        if '•' not in summary and len(summary) > 100:
            # Split long paragraphs into bullet points
            sentences = re.split(r'[.!?]+\s+', summary)
            if len(sentences) > 2:
                bullets = []
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 20:  # Skip very short fragments
                        bullets.append(f"• {sentence}")
                if bullets:
                    summary = '\n'.join(bullets)
        
        # Clean up excessive whitespace
        summary = re.sub(r'\n\s*\n\s*\n', '\n\n', summary)
        summary = re.sub(r' +', ' ', summary)
        
        # Ensure bullet points start on new lines
        summary = re.sub(r'([.!?])\s*•', r'\1\n•', summary)
        
        return summary.strip()
    
    def check_ollama_health(self) -> Dict[str, any]:
        """Check if Ollama service is available and healthy"""
        try:
            # Check if service is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                return {
                    'healthy': True,
                    'models_available': available_models,
                    'model_ready': self.model_name in available_models,
                    'error': None
                }
            else:
                return {
                    'healthy': False,
                    'error': f'Ollama returned status {response.status_code}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'healthy': False,
                'error': 'Cannot connect to Ollama service'
            }
        except requests.exceptions.Timeout:
            return {
                'healthy': False,
                'error': 'Ollama service timeout'
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': f'Health check failed: {str(e)}'
            }
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, any]]:
        """Get information about a specific model"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/show",
                json={"name": model_name},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
            return None
    
    def validate_transcript_length(self, transcript: str) -> bool:
        """Check if transcript length is within limits"""
        return len(transcript) <= self.max_transcript_length
    
    def extract_key_topics(self, summary: str) -> List[str]:
        """Extract key topics from a generated summary"""
        if not summary:
            return []
        
        topics = []
        
        # Simple keyword-based topic extraction
        # In production, you might want to use more sophisticated NLP
        topic_keywords = {
            "Programming": ["code", "programming", "software", "development", "algorithm"],
            "Machine Learning": ["machine learning", "ml", "ai", "neural", "model", "training"],
            "Web Development": ["web", "html", "css", "javascript", "frontend", "backend"],
            "Data Science": ["data", "analysis", "statistics", "visualization", "dataset"],
            "DevOps": ["deployment", "docker", "kubernetes", "ci/cd", "infrastructure"],
            "Security": ["security", "authentication", "encryption", "vulnerability"],
            "Database": ["database", "sql", "query", "table", "schema"],
            "Cloud": ["cloud", "aws", "azure", "gcp", "serverless"],
            "Mobile": ["mobile", "ios", "android", "app", "flutter", "react native"],
            "Design": ["design", "ui", "ux", "interface", "user experience"]
        }
        
        summary_lower = summary.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in summary_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def pull_model(self, model_name: str) -> Dict[str, any]:
        """Pull/download a model to Ollama"""
        try:
            logger.info(f"Pulling model: {model_name}")
            # If already present, return success (cached in persistent OLLAMA_HOME)
            health = self.check_ollama_health()
            existing = set(health.get('models_available', []) or [])
            if model_name in existing:
                return {
                    'success': True,
                    'message': f'Model already present: {model_name}',
                    'cached': True
                }
            
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=600  # 10 minutes for model download
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'Successfully pulled model: {model_name}',
                    'cached': False
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to pull model: {response.text}'
                }
                
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return {
                'success': False,
                'error': f'Failed to pull model: {str(e)}'
            }
    
    def set_model(self, model_name: str) -> bool:
        """Switch to a different model"""
        self.model_name = model_name
        return True

    def generate_jump_points(self, segments: List[Dict], transcript: str = "", model_name: Optional[str] = None, max_points: int = 10) -> List[Dict]:
        """Use the LLM to pick significant jump points from Whisper segments.

        Returns a list of {"seconds": int, "title": str}.
        Falls back to simple heuristics if the LLM is unavailable or parsing fails.
        """
        try:
            # Build concise candidates from segments into ~20s windows with short snippets
            candidates = []
            acc_text = []
            window_start = None
            last_end = None
            for seg in segments or []:
                try:
                    s = float(seg.get('start', 0))
                    e = float(seg.get('end', s))
                    text = (seg.get('text') or '').strip()
                except Exception:
                    continue
                if window_start is None:
                    window_start = s
                acc_text.append(text)
                last_end = e
                long_enough = (e - window_start) >= 20 or sum(len(t) for t in acc_text) >= 220
                if long_enough:
                    snippet = ' '.join(acc_text)
                    snippet = snippet.replace('\n', ' ').strip()
                    if snippet:
                        candidates.append({
                            'seconds': int(max(0, round(window_start))),
                            'snippet': snippet[:220]
                        })
                    acc_text = []
                    window_start = None
            if window_start is not None and acc_text:
                snippet = ' '.join(acc_text).replace('\n', ' ').strip()
                if snippet:
                    candidates.append({'seconds': int(max(0, round(window_start))), 'snippet': snippet[:220]})

            # Cap candidates to avoid overly long prompts
            if len(candidates) > 60:
                step = max(1, len(candidates) // 60)
                candidates = candidates[::step]

            # If we have too few candidates, just fall back to heuristics later
            if not candidates:
                return []

            # Prepare prompt
            def fmt_ts(sec: int) -> str:
                m = sec // 60
                s = sec % 60
                return f"{m}:{str(s).zfill(2)}"

            lines = [f"{fmt_ts(c['seconds'])} — {c['snippet']}" for c in candidates]
            guide = (
                "Select 6–12 truly significant moments that a viewer would want to jump to. "
                "Prefer topic changes, key demos, definitions, steps starting points, and conclusions. "
                "Spread them across the video (don’t cluster). "
                "Respond ONLY as JSON array with objects: {\"seconds\": <int>, \"title\": \"short label\"}."
            )
            prompt = (
                f"Transcript context (optional, truncated):\n{(transcript or '')[:2000]}\n\n"
                f"Candidate moments (time — snippet):\n" + "\n".join(lines) + "\n\n" + guide
            )

            # Check health
            health = self.check_ollama_health()
            model = model_name or self.model_name
            if health.get('healthy'):
                resp = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "top_p": 0.9,
                            "max_tokens": 800
                        }
                    },
                    timeout=600
                )
                if resp.status_code == 200:
                    text = resp.json().get('response', '')
                    # Extract first JSON array
                    import re
                    m = re.search(r"\[[\s\S]*\]", text)
                    if m:
                        try:
                            arr = json.loads(m.group(0))
                            out = []
                            for item in arr:
                                if not isinstance(item, dict):
                                    continue
                                sec = int(item.get('seconds') or 0)
                                title = str(item.get('title') or '').strip()
                                if sec >= 0 and title:
                                    out.append({"seconds": sec, "title": title[:100]})
                            # Enforce size limits and ordering
                            out = sorted(out, key=lambda x: x['seconds'])
                            if len(out) > max_points:
                                # Evenly downsample
                                step = max(1, len(out) // max_points)
                                out = out[::step][:max_points]
                            if out:
                                return out
                        except Exception:
                            pass

            # Fallback heuristic: evenly spaced key windows with keyword bias
            keywords = ("intro|introduction|overview|setup|install|configure|demo|example|concept|definition|"
                        "recap|summary|conclusion|next steps|best practice|tip|gotcha|issue|troubleshoot")
            import re
            scored = []
            for c in candidates:
                snip = c['snippet'].lower()
                score = 0
                if re.search(keywords, snip):
                    score += 2
                score += len(snip) / 200.0  # prefer meatier windows
                scored.append((score, c))
            scored.sort(key=lambda x: -x[0])
            # Take top 3 by score, then fill remaining evenly
            top = [c for _, c in scored[:3]]
            remaining = [c for _, c in scored[3:]]
            need = max(0, min(max_points, 10) - len(top))
            if need > 0 and remaining:
                step = max(1, len(remaining) // need)
                top.extend(remaining[::step][:need])
            # Sort and label
            top = sorted({c['seconds']: c for c in top}.values(), key=lambda x: x['seconds'])
            out = []
            for c in top:
                title = c['snippet'].split('. ')[0].strip()
                if len(title) > 80:
                    title = title[:77] + '...'
                out.append({"seconds": int(c['seconds']), "title": title})
            return out
        except Exception:
            return []
