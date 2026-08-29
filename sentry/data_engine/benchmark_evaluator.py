"""
Benchmark Evaluator and Metrics Suite for SENTRY.
Computes Equal Error Rate (EER), min t-DCF, ROC-AUC, FAR/FRR, and Confusion Matrices.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.metrics import roc_curve, roc_auc_score, precision_recall_fscore_support, confusion_matrix


class BenchmarkEvaluator:
    """Computes standardized speech deepfake and biometric verification metrics."""

    @staticmethod
    def compute_eer(y_true: np.ndarray, y_scores: np.ndarray) -> Tuple[float, float, np.ndarray, np.ndarray]:
        """
        Calculates the Equal Error Rate (EER) and operating threshold
        where False Acceptance Rate (FAR) == False Rejection Rate (FRR).
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_scores, pos_label=1)
        fnr = 1.0 - tpr

        # Find threshold where |FPR - FNR| is minimized
        idx_eer = np.nanargmin(np.abs(fpr - fnr))
        eer = float((fpr[idx_eer] + fnr[idx_eer]) / 2.0)
        optimal_threshold = float(thresholds[idx_eer])

        return eer, optimal_threshold, fpr, fnr

    @staticmethod
    def compute_min_tdcf(
        cm_scores: np.ndarray,
        cm_labels: np.ndarray,
        p_target: float = 0.05,
        p_spoof: float = 0.05,
        c_miss: float = 1.0,
        c_fa: float = 10.0
    ) -> float:
        """
        Computes normalized Minimum Tandem Detection Cost Function (min t-DCF)
        as standardized in ASVspoof 2019/2021 evaluations.
        """
        fpr, tpr, thresholds = roc_curve(cm_labels, cm_scores, pos_label=1)
        fnr = 1.0 - tpr

        # Tandem detection costs
        c_cm_miss = c_miss * p_target
        c_cm_fa = c_fa * p_spoof

        t_dcf_values = c_cm_miss * fnr + c_cm_fa * fpr
        # Normalize by default cost (min(c_miss, c_fa))
        min_cost = min(c_cm_miss, c_cm_fa)
        norm_tdcf = float(np.min(t_dcf_values) / max(min_cost, 1e-6))
        return round(norm_tdcf, 4)

    def evaluate_model_predictions(
        self,
        y_true: List[int],
        y_scores: List[float],
        threshold: float = 0.50
    ) -> Dict[str, Any]:
        """
        Computes complete performance report: EER, AUC, Precision, Recall, F1, and Confusion Matrix.
        """
        y_true_arr = np.array(y_true)
        y_scores_arr = np.array(y_scores)
        y_pred = (y_scores_arr >= threshold).astype(int)

        # 1. EER
        eer, opt_thresh, fpr, fnr = self.compute_eer(y_true_arr, y_scores_arr)

        # 2. ROC-AUC
        auc = float(roc_auc_score(y_true_arr, y_scores_arr))

        # 3. Precision, Recall, F1
        prec, rec, f1, _ = precision_recall_fscore_support(y_true_arr, y_pred, average="binary", zero_division=0)

        # 4. Confusion Matrix
        cm = confusion_matrix(y_true_arr, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)

        # 5. min t-DCF
        min_tdcf = self.compute_min_tdcf(y_scores_arr, y_true_arr)

        return {
            "equal_error_rate_pct": round(eer * 100.0, 2),
            "roc_auc_score": round(auc, 4),
            "min_tdcf": min_tdcf,
            "optimal_threshold": round(opt_thresh, 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "confusion_matrix": {
                "true_negatives_genuine": int(tn),
                "false_positives_false_alarm": int(fp),
                "false_negatives_missed_deepfake": int(fn),
                "true_positives_detected_clone": int(tp)
            },
            "far_pct": round(float(fp / max(tn + fp, 1)) * 100.0, 2),
            "frr_pct": round(float(fn / max(tp + fn, 1)) * 100.0, 2)
        }


benchmark_evaluator = BenchmarkEvaluator()
