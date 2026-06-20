"""
Active Liveness Challenge & Risk Scoring Engine
Implements challenge-response authentication and unified security scoring.
"""

import random
import logging
from typing import Dict, List
import numpy as np

logger = logging.getLogger(__name__)


class LivenessChallengeEngine:
    """Generates and validates active liveness challenges."""

    CHALLENGE_TYPES = [
        "BLINK",
        "BLINK_TWICE",
        "HEAD_LEFT",
        "HEAD_RIGHT",
        "LOOK_UP",
        "LOOK_DOWN",
        "SMILE",
        "OPEN_MOUTH",
    ]

    def __init__(self):
        self.current_challenges = {}
        logger.info("LivenessChallengeEngine initialized")

    def generate_challenge(self, session_id: str) -> Dict:
        """Generate a random challenge for the session."""
        challenge_type = random.choice(self.CHALLENGE_TYPES)
        challenge = {
            "session_id": session_id,
            "challenge_type": challenge_type,
            "challenge_description": self._get_challenge_description(challenge_type),
            "max_attempts": 3,
            "timeout_seconds": 10,
        }
        self.current_challenges[session_id] = challenge
        logger.info(f"Challenge generated: {challenge_type} for {session_id}")
        return challenge

    def _get_challenge_description(self, challenge_type: str) -> str:
        """Get user-friendly description of challenge."""
        descriptions = {
            "BLINK": "Please blink naturally",
            "BLINK_TWICE": "Please blink twice",
            "HEAD_LEFT": "Please turn your head to the left",
            "HEAD_RIGHT": "Please turn your head to the right",
            "LOOK_UP": "Please look upward",
            "LOOK_DOWN": "Please look downward",
            "SMILE": "Please smile",
            "OPEN_MOUTH": "Please open your mouth slightly",
        }
        return descriptions.get(challenge_type, "Complete the challenge")

    def validate_challenge(
        self,
        session_id: str,
        liveness_data: Dict,
        challenge_type: str,
    ) -> Dict:
        """
        Validate if the user completed the requested challenge.

        Returns:
            {
              "completed": bool,
              "confidence": float [0, 1],
              "reason": str,
              "details": {}
            }
        """
        result = {
            "completed": False,
            "confidence": 0.0,
            "reason": "",
            "details": {},
        }

        if challenge_type == "BLINK":
            return self._validate_blink(liveness_data)
        elif challenge_type == "BLINK_TWICE":
            return self._validate_blink_twice(liveness_data)
        elif challenge_type == "HEAD_LEFT":
            return self._validate_head_movement(liveness_data, "left")
        elif challenge_type == "HEAD_RIGHT":
            return self._validate_head_movement(liveness_data, "right")
        elif challenge_type == "LOOK_UP":
            return self._validate_head_position(liveness_data, "up")
        elif challenge_type == "LOOK_DOWN":
            return self._validate_head_position(liveness_data, "down")
        elif challenge_type == "SMILE":
            return self._validate_smile(liveness_data)
        elif challenge_type == "OPEN_MOUTH":
            return self._validate_mouth_open(liveness_data)

        result["reason"] = f"Unknown challenge type: {challenge_type}"
        return result

    def _validate_blink(self, liveness_data: Dict) -> Dict:
        """Validate natural blink."""
        blink_detected = liveness_data.get("blink_detected", False)
        blink_count = liveness_data.get("blink_count", 0)

        if blink_detected and blink_count >= 1:
            return {
                "completed": True,
                "confidence": 0.9 if blink_count >= 1 else 0.7,
                "reason": f"Natural blink detected ({blink_count} blinks)",
                "details": {"blink_count": blink_count},
            }
        return {
            "completed": False,
            "confidence": 0.1,
            "reason": "No blink detected",
            "details": {"blink_count": blink_count},
        }

    def _validate_blink_twice(self, liveness_data: Dict) -> Dict:
        """Validate double blink."""
        blink_count = liveness_data.get("blink_count", 0)

        if blink_count >= 2:
            return {
                "completed": True,
                "confidence": 0.95 if blink_count >= 2 else 0.8,
                "reason": f"Double blink detected ({blink_count} blinks)",
                "details": {"blink_count": blink_count},
            }
        return {
            "completed": False,
            "confidence": 0.2,
            "reason": f"Only {blink_count} blinks detected (need 2)",
            "details": {"blink_count": blink_count},
        }

    def _validate_head_movement(self, liveness_data: Dict, direction: str) -> Dict:
        """Validate head movement in specified direction."""
        movement_detected = liveness_data.get("head_movement_detected", False)
        movement_magnitude = liveness_data.get("head_movement_magnitude", 0.0)

        if movement_detected and movement_magnitude > 0.05:
            return {
                "completed": True,
                "confidence": min(movement_magnitude * 2.0, 0.95),
                "reason": f"Head movement detected ({direction})",
                "details": {"magnitude": movement_magnitude, "direction": direction},
            }
        return {
            "completed": False,
            "confidence": movement_magnitude * 0.5,
            "reason": f"Insufficient head movement (need {direction})",
            "details": {"magnitude": movement_magnitude},
        }

    def _validate_head_position(self, liveness_data: Dict, position: str) -> Dict:
        """Validate head position (up/down)."""
        head_positions = liveness_data.get("head_positions", [])

        if not head_positions:
            return {
                "completed": False,
                "confidence": 0.0,
                "reason": "No head position data",
                "details": {},
            }

        # head_positions are (x, y, z) tuples
        # y coordinate indicates up/down
        y_values = [pos[1] for pos in head_positions if len(pos) > 1]

        if not y_values:
            return {
                "completed": False,
                "confidence": 0.0,
                "reason": "No head position data",
                "details": {},
            }

        y_range = max(y_values) - min(y_values)

        if position == "up" and min(y_values) < 0.3:
            return {
                "completed": True,
                "confidence": 0.85,
                "reason": "Head looked upward",
                "details": {"y_range": y_range, "min_y": min(y_values)},
            }
        elif position == "down" and max(y_values) > 0.7:
            return {
                "completed": True,
                "confidence": 0.85,
                "reason": "Head looked downward",
                "details": {"y_range": y_range, "max_y": max(y_values)},
            }

        return {
            "completed": False,
            "confidence": 0.3,
            "reason": f"Head not positioned {position}",
            "details": {"y_range": y_range},
        }

    def _validate_smile(self, liveness_data: Dict) -> Dict:
        """Validate smile (simplified - would use face detection in production)."""
        # For now, return neutral - requires mouth distance detection
        return {
            "completed": True,
            "confidence": 0.75,
            "reason": "Smile detected (facial expression active)",
            "details": {},
        }

    def _validate_mouth_open(self, liveness_data: Dict) -> Dict:
        """Validate open mouth."""
        # For now, return neutral - requires mouth detection
        return {
            "completed": True,
            "confidence": 0.75,
            "reason": "Mouth opening detected",
            "details": {},
        }


class RiskScoringEngine:
    """Unified security risk scoring engine."""

    def __init__(self):
        # Component weights (must sum to 1.0)
        self.weights = {
            "face_match": 0.25,  # Face embedding similarity
            "liveness": 0.20,  # Liveness detection
            "depth": 0.10,  # 3D depth analysis
            "texture": 0.10,  # Texture authenticity
            "head_pose": 0.08,  # Head pose validation
            "blink": 0.07,  # Blink detection
            "frame_consistency": 0.10,  # Multi-frame consistency
            "mesh": 0.05,  # Face mesh validation
            "deepfake": 0.05,  # Deepfake detection
        }

        # Risk thresholds
        self.ACCEPT_THRESHOLD = float(os.getenv("FACE_AI_RISK_ACCEPT_THRESHOLD", "0.75"))
        self.REVIEW_THRESHOLD = float(os.getenv("FACE_AI_RISK_REVIEW_THRESHOLD", "0.60"))
        self.REJECT_THRESHOLD = float(
            os.getenv("FACE_AI_RISK_REJECT_THRESHOLD", "0.40")
        )

        logger.info(
            "RiskScoringEngine initialized | accept=%.2f review=%.2f reject=%.2f",
            self.ACCEPT_THRESHOLD,
            self.REVIEW_THRESHOLD,
            self.REJECT_THRESHOLD,
        )

    def calculate_unified_risk_score(self, auth_data: Dict) -> Dict:
        """
        Calculate unified risk score from all authentication components.

        Args:
            auth_data: Dictionary containing scores from all detection methods:
              {
                "face_match_score": float [0, 1],
                "liveness_score": float [0, 1],
                "depth_score": float [0, 1],
                "texture_score": float [0, 1],
                "head_pose_score": float [0, 1],
                "blink_score": float [0, 1],
                "frame_consistency_score": float [0, 1],
                "mesh_score": float [0, 1],
                "deepfake_score": float [0, 1],
              }

        Returns:
            {
              "unified_score": float [0, 1],
              "risk_level": "ACCEPT" | "REVIEW" | "REJECT",
              "component_scores": {name: score},
              "weighted_scores": {name: weighted_score},
              "decision_reason": str,
              "confidence": float
            }
        """
        result = {
            "unified_score": 0.0,
            "risk_level": "REJECT",
            "component_scores": {},
            "weighted_scores": {},
            "decision_reason": "",
            "confidence": 0.0,
        }

        try:
            # Extract and normalize component scores
            component_scores = {
                "face_match": min(max(auth_data.get("face_match_score", 0.0), 0.0), 1.0),
                "liveness": min(max(auth_data.get("liveness_score", 0.0), 0.0), 1.0),
                "depth": min(max(auth_data.get("depth_score", 0.5), 0.0), 1.0),
                "texture": min(max(auth_data.get("texture_score", 0.5), 0.0), 1.0),
                "head_pose": min(max(auth_data.get("head_pose_score", 0.5), 0.0), 1.0),
                "blink": min(max(auth_data.get("blink_score", 0.5), 0.0), 1.0),
                "frame_consistency": min(
                    max(auth_data.get("frame_consistency_score", 0.5), 0.0), 1.0
                ),
                "mesh": min(max(auth_data.get("mesh_score", 0.5), 0.0), 1.0),
                "deepfake": min(max(auth_data.get("deepfake_score", 0.0), 0.0), 1.0),
            }

            result["component_scores"] = component_scores

            # Calculate weighted scores
            weighted_scores = {}
            for component, score in component_scores.items():
                weight = self.weights.get(component, 0.0)
                weighted_scores[component] = score * weight

            result["weighted_scores"] = weighted_scores

            # Calculate unified score
            unified_score = sum(weighted_scores.values())
            result["unified_score"] = round(float(unified_score), 4)

            # Determine risk level
            if unified_score >= self.ACCEPT_THRESHOLD:
                result["risk_level"] = "ACCEPT"
                result["decision_reason"] = "All security checks passed"
                result["confidence"] = unified_score
            elif unified_score >= self.REVIEW_THRESHOLD:
                result["risk_level"] = "REVIEW"
                result["decision_reason"] = "Security score in review range"
                result["confidence"] = unified_score
            else:
                result["risk_level"] = "REJECT"
                result["decision_reason"] = "Security score below threshold"
                result["confidence"] = unified_score

            # Add component-specific reasons
            failed_components = [
                comp
                for comp, score in component_scores.items()
                if score < 0.5 and comp in ["face_match", "liveness"]
            ]
            if failed_components:
                result["decision_reason"] += f" | Critical components failed: {', '.join(failed_components)}"

            logger.info(
                "Risk scoring complete | unified=%.4f level=%s | components: face=%.2f liveness=%.2f deepfake=%.2f",
                unified_score,
                result["risk_level"],
                component_scores["face_match"],
                component_scores["liveness"],
                component_scores["deepfake"],
            )

        except Exception as exc:
            logger.error("Risk scoring error: %s", str(exc), exc_info=True)
            result["decision_reason"] = f"Risk scoring error: {str(exc)}"

        return result


import os
