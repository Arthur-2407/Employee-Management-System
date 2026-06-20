"""
Deepfake Detection Module
Detects deepfake attacks through temporal analysis, facial geometry validation,
and landmark stability checking across frame sequences.

Attack classes detected:
  - Facial reenactment deepfakes
  - GAN-generated synthetic faces
  - Expression-swapped videos
  - Lip-synced videos
"""

import cv2
import numpy as np
from typing import List, Dict
import logging
import os

try:
    import mediapipe as mp
    _MP_AVAILABLE = True
except ImportError:
    mp = None
    _MP_AVAILABLE = False

logger = logging.getLogger(__name__)


class DeepfakeDetector:
    """Detects deepfakes through multi-frame temporal analysis."""

    def __init__(self):
        if _MP_AVAILABLE:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        else:
            self.face_mesh = None
            logger.warning("mediapipe not available — deepfake detection disabled")

        # Thresholds for deepfake indicators
        self.LANDMARK_STABILITY_THRESHOLD = float(
            os.getenv("FACE_AI_LANDMARK_STABILITY_THRESHOLD", "0.08")
        )
        self.LIP_SYNC_ANOMALY_THRESHOLD = float(
            os.getenv("FACE_AI_LIP_SYNC_THRESHOLD", "0.15")
        )
        self.EYE_MOUTH_CORRELATION_THRESHOLD = float(
            os.getenv("FACE_AI_EYE_MOUTH_CORRELATION_THRESHOLD", "0.5")
        )
        self.TEMPORAL_ANOMALY_THRESHOLD = float(
            os.getenv("FACE_AI_TEMPORAL_ANOMALY_THRESHOLD", "0.12")
        )
        self.DEEPFAKE_CONFIDENCE_THRESHOLD = float(
            os.getenv("FACE_AI_DEEPFAKE_THRESHOLD", "0.65")
        )

        logger.info(
            "DeepfakeDetector initialised | thresholds: "
            "landmark_stability=%.3f lip_sync=%.3f eye_mouth=%.3f temporal=%.3f deepfake=%.2f",
            self.LANDMARK_STABILITY_THRESHOLD,
            self.LIP_SYNC_ANOMALY_THRESHOLD,
            self.EYE_MOUTH_CORRELATION_THRESHOLD,
            self.TEMPORAL_ANOMALY_THRESHOLD,
            self.DEEPFAKE_CONFIDENCE_THRESHOLD,
        )

    def analyze_deepfake_risk(self, face_frames: List[np.ndarray]) -> Dict:
        """
        Analyze multiple frames for deepfake indicators.

        Args:
            face_frames: List of cropped face images (BGR).

        Returns:
            {
              "deepfake_confidence": float [0, 1],
              "deepfake_suspected": bool,
              "landmark_stability": float,
              "landmark_stable": bool,
              "lip_sync_score": float,
              "lip_sync_anomaly": bool,
              "eye_mouth_correlation": float,
              "eye_mouth_correlated": bool,
              "temporal_consistency": float,
              "temporal_anomaly": bool,
              "face_mesh_variance": float,
              "mesh_anomaly": bool,
              "anomalies": [list of detected issues],
              "reasons": [str]
            }
        """
        if len(face_frames) < 3:
            return {
                "deepfake_confidence": 0.0,
                "deepfake_suspected": False,
                "landmark_stable": True,
                "lip_sync_anomaly": False,
                "eye_mouth_correlated": True,
                "temporal_anomaly": False,
                "mesh_anomaly": False,
                "anomalies": [],
                "reasons": ["Insufficient frames for deepfake analysis"],
            }

        results = {
            "deepfake_confidence": 0.0,
            "deepfake_suspected": False,
            "landmark_stability": 1.0,
            "landmark_stable": True,
            "lip_sync_score": 0.0,
            "lip_sync_anomaly": False,
            "eye_mouth_correlation": 1.0,
            "eye_mouth_correlated": True,
            "temporal_consistency": 1.0,
            "temporal_anomaly": False,
            "face_mesh_variance": 0.0,
            "mesh_anomaly": False,
            "anomalies": [],
            "reasons": [],
        }

        try:
            # Extract landmarks from all frames
            all_landmarks = []
            if self.face_mesh is not None:
                for frame in face_frames:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_result = self.face_mesh.process(rgb_frame)
                    if mp_result.multi_face_landmarks:
                        landmarks = mp_result.multi_face_landmarks[0]
                        all_landmarks.append(landmarks)
                    else:
                        all_landmarks.append(None)

                if len(all_landmarks) < 3 or all(lm is None for lm in all_landmarks):
                    results["reasons"].append("Could not extract landmarks")
                    return results

            # ── Method 1: Landmark Stability (Deepfakes show jitter)
            landmark_stability = self._analyze_landmark_stability(all_landmarks)
            results["landmark_stability"] = landmark_stability
            results["landmark_stable"] = landmark_stability > (1.0 - self.LANDMARK_STABILITY_THRESHOLD)
            if not results["landmark_stable"]:
                results["anomalies"].append("LANDMARK_INSTABILITY")
                results["reasons"].append("Excessive landmark jitter detected")

            # ── Method 2: Lip Sync Analysis (Deepfakes have lip-sync artifacts)
            lip_sync_score = self._analyze_lip_sync(all_landmarks)
            results["lip_sync_score"] = lip_sync_score
            results["lip_sync_anomaly"] = lip_sync_score > self.LIP_SYNC_ANOMALY_THRESHOLD
            if results["lip_sync_anomaly"]:
                results["anomalies"].append("LIP_SYNC_ANOMALY")
                results["reasons"].append("Unnatural lip-sync pattern detected")

            # ── Method 3: Eye-Mouth Correlation (Should be correlated in real faces)
            eye_mouth_corr = self._analyze_eye_mouth_correlation(all_landmarks)
            results["eye_mouth_correlation"] = eye_mouth_corr
            results["eye_mouth_correlated"] = eye_mouth_corr > self.EYE_MOUTH_CORRELATION_THRESHOLD
            if not results["eye_mouth_correlated"]:
                results["anomalies"].append("EYE_MOUTH_MISMATCH")
                results["reasons"].append("Eye-mouth correlation anomaly detected")

            # ── Method 4: Temporal Consistency (Deepfakes have temporal artifacts)
            temporal_consistency = self._analyze_temporal_consistency(all_landmarks)
            results["temporal_consistency"] = temporal_consistency
            results["temporal_anomaly"] = temporal_consistency < (1.0 - self.TEMPORAL_ANOMALY_THRESHOLD)
            if results["temporal_anomaly"]:
                results["anomalies"].append("TEMPORAL_INCONSISTENCY")
                results["reasons"].append("Unnatural temporal changes detected")

            # ── Method 5: Face Mesh Geometry Variance
            mesh_variance = self._analyze_mesh_geometry_variance(all_landmarks)
            results["face_mesh_variance"] = mesh_variance
            results["mesh_anomaly"] = mesh_variance > 0.15  # Excessive geometric changes
            if results["mesh_anomaly"]:
                results["anomalies"].append("MESH_GEOMETRY_ANOMALY")
                results["reasons"].append("Abnormal face geometry changes")

            # ── Unified Deepfake Confidence
            anomaly_count = len(results["anomalies"])
            if anomaly_count == 0:
                results["deepfake_confidence"] = 0.0
            elif anomaly_count == 1:
                results["deepfake_confidence"] = 0.30
            elif anomaly_count == 2:
                results["deepfake_confidence"] = 0.55
            elif anomaly_count >= 3:
                results["deepfake_confidence"] = min(0.75 + (0.05 * (anomaly_count - 3)), 1.0)

            results["deepfake_suspected"] = (
                results["deepfake_confidence"] > self.DEEPFAKE_CONFIDENCE_THRESHOLD
            )

            logger.info(
                "Deepfake analysis | confidence=%.4f suspected=%s anomalies=%s",
                results["deepfake_confidence"],
                results["deepfake_suspected"],
                results["anomalies"],
            )

        except Exception as exc:
            logger.error("Deepfake analysis error: %s", str(exc), exc_info=True)
            results["reasons"].append(f"Analysis error: {str(exc)}")

        return results

    def _analyze_landmark_stability(self, landmarks_list: List) -> float:
        """Measure landmark position stability across frames (lower = more stable)."""
        if len(landmarks_list) < 2 or any(lm is None for lm in landmarks_list):
            return 1.0

        try:
            displacements = []
            for i in range(len(landmarks_list) - 1):
                if landmarks_list[i] is None or landmarks_list[i + 1] is None:
                    continue

                curr_pts = np.array(
                    [(lm.x, lm.y) for lm in landmarks_list[i].landmark]
                )
                next_pts = np.array(
                    [(lm.x, lm.y) for lm in landmarks_list[i + 1].landmark]
                )
                displacement = np.mean(np.linalg.norm(curr_pts - next_pts, axis=1))
                displacements.append(displacement)

            if not displacements:
                return 1.0

            # Stability: inverse of mean displacement (lower displacement = higher stability)
            mean_displacement = np.mean(displacements)
            stability = max(0.0, 1.0 - mean_displacement * 5.0)  # Scale for reasonable range
            return float(stability)

        except Exception as exc:
            logger.error("Landmark stability analysis error: %s", str(exc))
            return 1.0

    def _analyze_lip_sync(self, landmarks_list: List) -> float:
        """Detect lip-sync anomalies (lips don't match natural speech timing)."""
        if len(landmarks_list) < 3 or any(lm is None for lm in landmarks_list):
            return 0.0

        try:
            lip_openness_values = []
            for landmarks in landmarks_list:
                if landmarks is None:
                    continue
                # Lips indices (MediaPipe)
                upper_lip_idx = 12  # Upper lip
                lower_lip_idx = 14  # Lower lip
                upper_lip = landmarks.landmark[upper_lip_idx]
                lower_lip = landmarks.landmark[lower_lip_idx]
                lip_openness = abs(lower_lip.y - upper_lip.y)
                lip_openness_values.append(lip_openness)

            if len(lip_openness_values) < 2:
                return 0.0

            # Detect unnatural patterns (too regular or too irregular)
            lip_changes = np.abs(np.diff(lip_openness_values))
            mean_change = np.mean(lip_changes)
            std_change = np.std(lip_changes)

            # Anomaly if: too regular (std close to 0) or too erratic (std very high)
            if std_change < 0.003:
                return 0.15  # Too regular
            elif std_change > 0.08:
                return 0.08  # Too erratic
            else:
                return 0.0  # Normal variation

        except Exception as exc:
            logger.error("Lip-sync analysis error: %s", str(exc))
            return 0.0

    def _analyze_eye_mouth_correlation(self, landmarks_list: List) -> float:
        """
        Analyze eye-mouth correlation (in real faces, eyes and mouth often move together).
        """
        if len(landmarks_list) < 3 or any(lm is None for lm in landmarks_list):
            return 0.5

        try:
            eye_variations = []
            mouth_variations = []

            for landmarks in landmarks_list:
                if landmarks is None:
                    continue

                # Eye openness (left + right eye)
                left_eye_top = landmarks.landmark[159].y  # Top of left eye
                left_eye_bottom = landmarks.landmark[145].y  # Bottom of left eye
                right_eye_top = landmarks.landmark[386].y
                right_eye_bottom = landmarks.landmark[374].y
                eye_openness = (
                    abs(left_eye_bottom - left_eye_top)
                    + abs(right_eye_bottom - right_eye_top)
                ) / 2.0
                eye_variations.append(eye_openness)

                # Mouth openness
                mouth_top = landmarks.landmark[12].y
                mouth_bottom = landmarks.landmark[14].y
                mouth_openness = abs(mouth_bottom - mouth_top)
                mouth_variations.append(mouth_openness)

            if len(eye_variations) < 2 or len(mouth_variations) < 2:
                return 0.5

            # Calculate correlation
            eye_arr = np.array(eye_variations)
            mouth_arr = np.array(mouth_variations)
            correlation = float(
                np.corrcoef(eye_arr, mouth_arr)[0, 1]
                if not np.isnan(np.corrcoef(eye_arr, mouth_arr)[0, 1])
                else 0.0
            )
            # Normalize: real faces should have positive correlation
            return max(correlation, 0.0)

        except Exception as exc:
            logger.error("Eye-mouth correlation error: %s", str(exc))
            return 0.5

    def _analyze_temporal_consistency(self, landmarks_list: List) -> float:
        """Measure temporal smoothness (should be smooth for real faces)."""
        if len(landmarks_list) < 3 or any(lm is None for lm in landmarks_list):
            return 1.0

        try:
            accelerations = []
            prev_velocity = None

            for i in range(len(landmarks_list) - 2):
                if landmarks_list[i] is None or landmarks_list[i + 1] is None or landmarks_list[i + 2] is None:
                    continue

                # Get nose position (central landmark)
                curr_nose = landmarks_list[i].landmark[1]
                next_nose = landmarks_list[i + 1].landmark[1]
                next_next_nose = landmarks_list[i + 2].landmark[1]

                velocity1 = np.array([next_nose.x - curr_nose.x, next_nose.y - curr_nose.y])
                velocity2 = np.array(
                    [next_next_nose.x - next_nose.x, next_next_nose.y - next_nose.y]
                )

                acceleration = np.linalg.norm(velocity2 - velocity1)
                accelerations.append(acceleration)

            if not accelerations:
                return 1.0

            # Consistency: inverse of mean acceleration (lower acceleration = more consistent)
            mean_accel = np.mean(accelerations)
            consistency = max(0.0, 1.0 - mean_accel * 3.0)
            return float(consistency)

        except Exception as exc:
            logger.error("Temporal consistency error: %s", str(exc))
            return 1.0

    def _analyze_mesh_geometry_variance(self, landmarks_list: List) -> float:
        """Detect abnormal changes in facial geometry (deepfakes show geometry warping)."""
        if len(landmarks_list) < 2 or any(lm is None for lm in landmarks_list):
            return 0.0

        try:
            geometry_changes = []

            for i in range(len(landmarks_list) - 1):
                if landmarks_list[i] is None or landmarks_list[i + 1] is None:
                    continue

                # Extract key facial dimensions
                face_width_1 = (
                    landmarks_list[i].landmark[454].x - landmarks_list[i].landmark[234].x
                )  # Ears
                face_width_2 = (
                    landmarks_list[i + 1].landmark[454].x
                    - landmarks_list[i + 1].landmark[234].x
                )

                face_height_1 = (
                    landmarks_list[i].landmark[152].y - landmarks_list[i].landmark[10].y
                )  # Chin to forehead
                face_height_2 = (
                    landmarks_list[i + 1].landmark[152].y
                    - landmarks_list[i + 1].landmark[10].y
                )

                width_change = abs(face_width_2 - face_width_1) / (face_width_1 + 1e-7)
                height_change = abs(face_height_2 - face_height_1) / (face_height_1 + 1e-7)

                geometry_changes.append((width_change + height_change) / 2.0)

            if not geometry_changes:
                return 0.0

            # Deepfakes show larger geometric changes than natural face movement
            mean_change = np.mean(geometry_changes)
            return min(float(mean_change), 1.0)

        except Exception as exc:
            logger.error("Mesh geometry variance error: %s", str(exc))
            return 0.0
