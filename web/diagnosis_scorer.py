"""
Smart Diagnosis Scoring System
Hệ thống chấm điểm thông minh cho chẩn đoán y tế.
"""

from typing import Set, List, Dict, Tuple, Optional


class SmartDiagnosisScorer:
    """Hệ thống chấm điểm thông minh cho chẩn đoán y tế."""

    def __init__(self):
        # Trọng số triệu chứng cho từng bệnh (0.0 - 1.0)
        # 1.0 = triệu chứng đặc trưng rất cao
        # 0.5 = triệu chứng phổ biến
        # -0.3 = triệu chứng trái ngược (unlikely)
        self.symptom_weights = {
            "cam_thuong": {
                # Triệu chứng chính
                "sot": 0.75,
                "ho": 0.85,
                "chay_mui": 0.80,
                "dau_hong": 0.70,
                "dau_dau": 0.60,
                "met_moi": 0.55,
                "nhiet_do_cao": 0.65,
                # Triệu chứng phản bác
                "kho_tho": -0.30,
                "spo2_thap": -0.50,
                "mat_vi_giac": -0.40,
                "mat_khu_giac": -0.40,
                "ho_ra_mau": -0.60,
            },
            "covid_19": {
                # Triệu chứng đặc trưng
                "mat_vi_giac": 0.95,
                "mat_khu_giac": 0.95,
                "sot": 0.85,
                "ho": 0.80,
                "kho_tho": 0.85,
                "met_moi": 0.75,
                "dau_dau": 0.70,
                "sot_cao": 0.80,
                # Triệu chứng thêm
                "dau_hong": 0.60,
                "chay_mui": 0.55,
            },
            "nghi_covid": {
                # Tương tự covid nhưng ít chắc chắn hơn
                "mat_vi_giac": 0.90,
                "mat_khu_giac": 0.90,
                "sot": 0.80,
                "ho": 0.75,
                "kho_tho": 0.80,
                "met_moi": 0.70,
                "dau_dau": 0.65,
            },
            "viem_phoi": {
                # Triệu chứng nghiêm trọng
                "sot_cao": 0.90,
                "ho_co_dam": 0.90,
                "kho_tho": 0.95,
                "dau_nguc": 0.85,
                "spo2_thap": 0.90,
                "ho_ra_mau": 0.85,
                # Triệu chứng phụ
                "met_moi": 0.70,
                "ho": 0.75,
                "sot": 0.80,
                "nhiet_do_cao": 0.85,
            },
            "viem_hong": {
                "dau_hong": 0.95,
                "kho_nuot": 0.90,
                "sot": 0.70,
                "ho": 0.65,
                "met_moi": 0.55,
                "nhiet_do_cao": 0.60,
                "chay_mui": 0.50,
            },
            "hen_suyen": {
                "kho_tho": 0.95,
                "tho_khoe_khe": 0.90,
                "ho": 0.75,
                "co_kich_thich": 0.80,
                "dau_nguc": 0.60,
            },
            "viem_da_day": {
                "dau_bung": 0.90,
                "buon_non": 0.85,
                "dau_lau_ngay": 0.80,
                "non_sau_an": 0.85,
                "an_khong_tieu": 0.75,
                # Phản bác
                "ho": -0.30,
                "kho_tho": -0.40,
                "chay_mui": -0.20,
            },
            "ngo_doc_thuc_pham": {
                "buon_non": 0.95,
                "tieu_chay": 0.95,
                "dau_bung": 0.90,
                "non_ra_mau": 0.85,
                "sot": 0.65,
                "met_moi": 0.60,
            },
        }

        # Prior probability (xác suất tiền nghiệm từ thống kê y tế)
        self.priors = {
            "cam_thuong": 0.20,  # 20% - rất phổ biến
            "viem_hong": 0.12,  # 12% - khá phổ biến
            "covid_19": 0.08,  # 8% - phụ thuộc dịch
            "nghi_covid": 0.06,  # 6%
            "viem_phoi": 0.03,  # 3% - ít hơn
            "hen_suyen": 0.05,  # 5% - khá phổ biến
            "viem_da_day": 0.08,  # 8%
            "ngo_doc_thuc_pham": 0.02,  # 2% - hiếm
        }

        # Severity penalties (phạt khi có triệu chứng nghiêm trọng nhưng chẩn đoán bệnh nhẹ)
        self.severity_penalties = {
            "cam_thuong": {
                "kho_tho": 25,
                "spo2_thap": 30,
                "ho_ra_mau": 35,
                "sot_cao": 15,
            },
            "viem_hong": {
                "kho_tho": 20,
                "spo2_thap": 25,
                "ho_ra_mau": 30,
            },
            "nghi_covid": {
                "spo2_thap": 15,
                "ho_ra_mau": 20,
            },
        }

        # Bonuses (thưởng khi có tổ hợp triệu chứng đặc trưng)
        self.combo_bonuses = {
            "covid_19": [
                ({"mat_vi_giac", "mat_khu_giac"}, 20),  # Cặp đôi đặc trưng
                ({"sot", "ho", "kho_tho"}, 15),
                ({"mat_vi_giac", "sot", "ho"}, 18),
            ],
            "nghi_covid": [
                ({"mat_vi_giac", "mat_khu_giac"}, 18),
                ({"sot", "ho", "kho_tho"}, 12),
            ],
            "viem_phoi": [
                ({"sot_cao", "kho_tho", "ho_co_dam"}, 20),
                ({"kho_tho", "dau_nguc", "spo2_thap"}, 25),
                ({"sot_cao", "kho_tho"}, 15),
            ],
            "ngo_doc_thuc_pham": [
                ({"buon_non", "tieu_chay", "dau_bung"}, 20),
                ({"buon_non", "tieu_chay"}, 12),
            ],
        }

    def calculate_score(self, disease: str, symptoms: Set[str]) -> float:
        """Tính điểm confidence thông minh cho một bệnh.

        Args:
            disease: Tên bệnh
            symptoms: Tập triệu chứng

        Returns:
            float: Điểm confidence (0-100)
        """
        if disease not in self.symptom_weights:
            return 0.0

        weights = self.symptom_weights[disease]
        prior = self.priors.get(disease, 0.05)

        # 1. Evidence Accumulation (tích lũy bằng chứng)
        positive_evidence = 0.0
        negative_evidence = 0.0
        max_possible_positive = 0.0

        for symptom, weight in weights.items():
            if weight > 0:
                max_possible_positive += weight
                if symptom in symptoms:
                    positive_evidence += weight
            else:  # weight < 0
                if symptom in symptoms:
                    negative_evidence += abs(weight)

        # Tỷ lệ bằng chứng dương
        positive_ratio = (
            positive_evidence / max_possible_positive
            if max_possible_positive > 0
            else 0
        )

        # Base score từ evidence - Tăng lên để không quá thấp
        base_score = positive_ratio * 70  # Tăng từ 60 -> 70 điểm

        # 2. Penalty từ bằng chứng phủ định
        penalty = negative_evidence * 15  # Giảm penalty từ 20 -> 15

        # 3. Bonus từ prior probability
        prior_bonus = prior * 25  # Tăng từ 20 -> 25 để ưu tiên bệnh phổ biến hơn

        # 4. Severity penalty (phạt nếu bệnh nhẹ nhưng có triệu chứng nặng)
        severity_penalty = 0
        if disease in self.severity_penalties:
            for symptom, penalty_value in self.severity_penalties[disease].items():
                if symptom in symptoms:
                    severity_penalty += penalty_value

        # 5. Combo bonus (thưởng nếu có tổ hợp đặc trưng)
        combo_bonus = 0
        if disease in self.combo_bonuses:
            for combo_symptoms, bonus_value in self.combo_bonuses[disease]:
                if combo_symptoms.issubset(symptoms):
                    combo_bonus += bonus_value

        # 6. Symptom count adjustment (điều chỉnh theo số triệu chứng)
        symptom_count = len(symptoms)
        count_adjustment = 0

        if disease == "cam_thuong" and symptom_count > 7:
            # Cảm cúm với quá nhiều triệu chứng -> giảm confidence
            count_adjustment = -(symptom_count - 7) * 3
        elif disease in ["viem_phoi", "covid_19"] and symptom_count >= 5:
            # Bệnh nặng với nhiều triệu chứng -> tăng confidence
            count_adjustment = min(15, (symptom_count - 4) * 3)  # Tăng bonus
        elif symptom_count >= 4:
            # Các bệnh khác với 4+ triệu chứng -> bonus nhỏ
            count_adjustment = min(10, (symptom_count - 3) * 2)

        # Tổng hợp điểm
        final_score = (
            base_score
            + prior_bonus
            + combo_bonus
            + count_adjustment
            - penalty
            - severity_penalty
        )

        # Bonus nếu match nhiều triệu chứng quan trọng
        if positive_ratio >= 0.7:  # Match >= 70% triệu chứng
            final_score += 10
        elif positive_ratio >= 0.5:  # Match >= 50%
            final_score += 5

        # Áp dụng hard limits theo từng bệnh
        if disease == "cam_thuong":
            # Cảm cúm không thể quá 80%
            final_score = min(final_score, 80)
            # Nếu có nhiều triệu chứng nghiêm trọng -> max 55%
            severe_symptoms = {"kho_tho", "spo2_thap", "ho_ra_mau", "sot_cao"}
            severe_count = len([s for s in symptoms if s in severe_symptoms])
            if severe_count >= 2:
                final_score = min(final_score, 55)
            elif severe_count == 1:
                final_score = min(final_score, 70)
        elif disease == "viem_hong":
            # Viêm họng max 85% nếu không có triệu chứng đặc trưng rất rõ
            if "kho_nuot" not in symptoms:
                final_score = min(final_score, 85)
        else:
            # Các bệnh khác max 95%
            final_score = min(final_score, 95)

        # Minimum score
        final_score = max(final_score, 0)

        return round(final_score, 1)

    def diagnose(
        self, symptoms: Set[str], inference_diseases: List[str]
    ) -> Tuple[Optional[str], float, List[Dict]]:
        """Chẩn đoán thông minh.

        Args:
            symptoms: Tập triệu chứng
            inference_diseases: Các bệnh từ inference engine

        Returns:
            tuple: (disease, confidence, all_candidates)
                - disease: Bệnh được chẩn đoán (hoặc None)
                - confidence: Độ tin cậy (0-100)
                - all_candidates: Danh sách tất cả ứng viên
        """
        candidates = []

        for disease in inference_diseases:
            score = self.calculate_score(disease, symptoms)
            if score > 0:
                candidates.append(
                    {
                        "disease": disease,
                        "confidence": score,
                        "symptom_count": len(symptoms),
                    }
                )

        # Sort by confidence (cao nhất trước)
        candidates.sort(key=lambda x: x["confidence"], reverse=True)

        if not candidates:
            return None, 0.0, []

        best = candidates[0]
        return best["disease"], best["confidence"], candidates

    def explain_diagnosis(self, disease: str, symptoms: Set[str]) -> Dict:
        """Giải thích tại sao chọn bệnh này.

        Args:
            disease: Tên bệnh
            symptoms: Tập triệu chứng

        Returns:
            dict: Thông tin giải thích chi tiết
        """
        if disease not in self.symptom_weights:
            return {}

        weights = self.symptom_weights[disease]

        # Phân loại triệu chứng
        matched_positive = []
        matched_negative = []
        missing_important = []

        for symptom, weight in weights.items():
            if symptom in symptoms:
                if weight > 0:
                    matched_positive.append((symptom, weight))
                else:
                    matched_negative.append((symptom, abs(weight)))
            elif weight > 0.7:  # Triệu chứng quan trọng nhưng không có
                missing_important.append((symptom, weight))

        # Sắp xếp theo trọng số
        matched_positive.sort(key=lambda x: x[1], reverse=True)
        matched_negative.sort(key=lambda x: x[1], reverse=True)
        missing_important.sort(key=lambda x: x[1], reverse=True)

        return {
            "matched_positive": matched_positive[:5],  # Top 5
            "matched_negative": matched_negative,
            "missing_important": missing_important[:3],  # Top 3
        }
