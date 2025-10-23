"""Medical Routes - User-facing medical diagnosis interface.

This blueprint provides a user-friendly medical diagnosis system where users can:
- Input symptoms through an intuitive wizard form
- Get AI-powered diagnosis based on 100 medical rules
- Receive treatment recommendations
- View visualization of inference process
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set
from uuid import uuid4

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    url_for,
)

from inference_lab.forward import run_forward_inference
from inference_lab.graphs import GRAPHVIZ_AVAILABLE

# Import Smart Diagnosis Scorer
from inference_lab.web.diagnosis_scorer import SmartDiagnosisScorer

# Import Medical KB
try:
    from medical_kb import MedicalKnowledgeBase, extract_facts_from_form
except ImportError:
    MedicalKnowledgeBase = None
    extract_facts_from_form = None


# Create blueprint
medical_bp = Blueprint(
    "medical",
    __name__,
    url_prefix="/medical",
    template_folder="../templates/medical",
    static_folder="../static/medical",
    static_url_path="/static",
)


# Global KB instance (loaded once)
_medical_kb = None


def get_medical_kb() -> Any:
    """Get or create Medical KB instance."""
    global _medical_kb
    if _medical_kb is None:
        if MedicalKnowledgeBase is None:
            raise RuntimeError(
                "Medical KB not available. Please ensure medical_kb module is installed."
            )
        _medical_kb = MedicalKnowledgeBase()
    return _medical_kb


def _analyze_symptoms_without_diagnosis(
    input_facts: Set[str], final_facts: List[str]
) -> Dict[str, Any]:
    """Phân tích triệu chứng khi không chẩn đoán được bệnh cụ thể.

    Args:
        input_facts: Triệu chứng ban đầu từ người dùng
        final_facts: Các facts sau khi inference

    Returns:
        Dict chứa phân tích: category, severity_indicators, suggestions
    """
    analysis = {"categories": [], "severity_indicators": [], "suggestions": []}

    # Phân loại triệu chứng theo hệ thống cơ thể
    symptom_categories = {
        "respiratory": [
            "ho",
            "kho_tho",
            "chay_mui",
            "dau_hong",
            "ho_co_dam",
            "ho_khan",
        ],
        "digestive": ["dau_bung", "buon_non", "tieu_chay", "non_ra_mau", "phan_co_mau"],
        "neurological": ["dau_dau", "choang_vang", "mat_vi_giac", "mat_khu_giac"],
        "cardiovascular": ["dau_nguc", "tim_dap_nhanh", "tim_dap_cham", "ra_mo_hoi"],
        "general": ["sot", "met_moi", "sot_cao", "nhiet_do_cao"],
    }

    category_names = {
        "respiratory": "Hô hấp",
        "digestive": "Tiêu hóa",
        "neurological": "Thần kinh",
        "cardiovascular": "Tim mạch",
        "general": "Toàn thân",
    }

    # Xác định các hệ thống bị ảnh hưởng
    for category, symptoms in symptom_categories.items():
        if any(s in input_facts for s in symptoms):
            analysis["categories"].append(category_names[category])

    # Xác định mức độ nghiêm trọng
    severe_symptoms = {
        "kho_tho_nang",
        "dau_nguc",
        "sot_cao",
        "non_ra_mau",
        "phan_co_mau",
        "choang_vang",
    }
    if any(s in final_facts for s in severe_symptoms):
        analysis["severity_indicators"].append("Có triệu chứng cần chú ý")

    # Đưa ra gợi ý dựa trên category
    if "Hô hấp" in analysis["categories"]:
        analysis["suggestions"].append("Có thể liên quan đến bệnh về đường hô hấp")
    if "Tiêu hóa" in analysis["categories"]:
        analysis["suggestions"].append("Có thể liên quan đến vấn đề tiêu hóa")
    if len(analysis["categories"]) >= 2:
        analysis["suggestions"].append(
            "Triệu chứng ảnh hưởng nhiều hệ thống - cần khám toàn diện"
        )

    return analysis


def _generate_symptom_based_recommendation(
    input_facts: Set[str], final_facts: List[str], analysis: Dict[str, Any]
) -> str:
    """Tạo khuyến nghị dựa trên triệu chứng khi không chẩn đoán được bệnh cụ thể.

    Args:
        input_facts: Triệu chứng ban đầu
        final_facts: Facts sau inference
        analysis: Kết quả phân tích từ _analyze_symptoms_without_diagnosis

    Returns:
        Chuỗi khuyến nghị
    """
    recommendations = []

    # Khuyến nghị chung
    recommendations.append("🏥 **Khám bác sĩ để được chẩn đoán chính xác**")
    recommendations.append("   - Triệu chứng hiện tại chưa đủ để xác định bệnh cụ thể")
    recommendations.append("   - Cần thêm thông tin và xét nghiệm y tế")

    # Khuyến nghị theo category
    if "Hô hấp" in analysis["categories"]:
        recommendations.append("🫁 **Chăm sóc hệ hô hấp:**")
        recommendations.append("   - Nghỉ ngơi đầy đủ, tránh khói bụi")
        recommendations.append("   - Uống đủ nước, giữ ấm cơ thể")

    if "Tiêu hóa" in analysis["categories"]:
        recommendations.append("🍵 **Chăm sóc tiêu hóa:**")
        recommendations.append("   - Uống nhiều nước để tránh mất nước")
        recommendations.append("   - Ăn nhẹ, dễ tiêu, tránh thức ăn cay nóng")

    if "Thần kinh" in analysis["categories"]:
        recommendations.append("🧠 **Chú ý triệu chứng thần kinh:**")
        recommendations.append("   - Nghỉ ngơi trong môi trường yên tĩnh")
        recommendations.append("   - Theo dõi sát, nếu nặng hơn hãy đến bác sĩ ngay")

    if "Tim mạch" in analysis["categories"]:
        recommendations.append("❤️ **Cảnh báo triệu chứng tim mạch:**")
        recommendations.append("   - Cần được khám ngay nếu có đau ngực, khó thở")
        recommendations.append("   - Không tự ý vận động mạnh")

    # Khuyến nghị về severity
    if analysis["severity_indicators"]:
        recommendations.append("⚠️ **Lưu ý quan trọng:**")
        recommendations.append("   - Có dấu hiệu cần theo dõi sát")
        recommendations.append("   - Đến cơ sở y tế nếu triệu chứng nặng hơn")
        recommendations.append("   - Gọi 115 trong trường hợp khẩn cấp")

    # Khuyến nghị chung cuối
    recommendations.append("📝 **Ghi chú thêm:**")
    recommendations.append("   - Theo dõi nhiệt độ, diễn biến triệu chứng")
    recommendations.append("   - Chuẩn bị thông tin chi tiết khi gặp bác sĩ")
    recommendations.append("   - Không tự ý dùng thuốc kháng sinh")

    return "\n".join(recommendations)


@medical_bp.get("/")
def landing():
    """Medical landing page."""
    try:
        kb = get_medical_kb()
        metadata = kb.get_metadata()
    except Exception:
        metadata = {"total_rules": 100, "modules": []}

    return render_template(
        "landing.html",
        metadata=metadata,
        graphviz_available=GRAPHVIZ_AVAILABLE,
        current_year=datetime.now().year,
    )


@medical_bp.get("/check")
def check():
    """Medical symptom input wizard."""
    try:
        kb = get_medical_kb()
        form_fields = kb.get_form_fields()
    except Exception as e:
        return (
            render_template("error.html", error=f"Could not load Medical KB: {e}"),
            500,
        )

    return render_template(
        "wizard.html",
        form_fields=form_fields,
        current_year=datetime.now().year,
    )


@medical_bp.post("/api/diagnose")
def api_diagnose():
    """Diagnose based on symptoms."""
    payload = request.get_json(silent=True) or {}

    try:
        kb = get_medical_kb()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    # Extract form data - accept both direct data or wrapped in "symptoms" key
    form_data = payload.get("symptoms", payload) if "symptoms" in payload else payload

    # Debug logging
    print(f"[DEBUG] Received form_data: {form_data}")

    if not form_data or (isinstance(form_data, dict) and not any(form_data.values())):
        return jsonify({"ok": False, "error": "No symptoms provided"}), 400

    # Convert form data to facts
    try:
        if extract_facts_from_form:
            facts = extract_facts_from_form(form_data, kb)
        else:
            # Fallback: simple extraction
            facts = _simple_extract_facts(form_data)

        print(f"[DEBUG] Extracted facts: {facts}")

        if not facts:
            return (
                jsonify(
                    {
                        "ok": False,
                        "error": "Không thể xác định triệu chứng từ dữ liệu đầu vào",
                    }
                ),
                400,
            )

    except Exception as e:
        print(f"[DEBUG] Error extracting facts: {e}")
        return jsonify({"ok": False, "error": f"Error extracting facts: {e}"}), 400

    # Run inference
    session_id = uuid4().hex
    output_root = Path(
        current_app.config.get(
            "GRAPH_OUTPUT_ROOT", "inference_lab/web/static/generated"
        )
    )
    output_dir = output_root / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Get possible diseases as goals
        goals = _get_possible_diseases(kb)

        # Run forward inference
        print(f"[DEBUG] Running inference with facts: {facts}")
        print(f"[DEBUG] Goals: {goals}")
        result = run_forward_inference(
            kb.kb,  # Use the internal KnowledgeBase
            initial_facts=facts,
            goals=goals,
            strategy="stack",
            index_mode="min",
            make_graphs=False,  # Tắt tạo đồ thị để tối ưu performance
            output_dir=output_dir,
        )

        print(f"[DEBUG] Inference result success: {result.success}")
        print(f"[DEBUG] Final facts: {result.final_facts}")
        print(f"[DEBUG] Fired rules: {result.fired_rules}")
        print(
            f"[DEBUG] Graph files: {result.graph_files if hasattr(result, 'graph_files') else 'No graph_files attr'}"
        )

        # === SMART DIAGNOSIS với Weighted Scoring System ===
        # Khởi tạo Smart Diagnosis Scorer
        scorer = SmartDiagnosisScorer()

        # Lấy danh sách bệnh từ inference engine
        inference_diseases = [goal for goal in goals if goal in result.final_facts]

        print(f"[DEBUG] Diseases detected by inference: {inference_diseases}")

        # Chẩn đoán thông minh với weighted scoring
        diagnosed_disease, confidence, disease_candidates = scorer.diagnose(
            facts, inference_diseases
        )

        # Debug log top candidates
        print(f"[SMART DIAGNOSIS] Total candidates: {len(disease_candidates)}")
        if disease_candidates:
            print(f"[SMART DIAGNOSIS] Top 3 candidates:")
            for i, candidate in enumerate(disease_candidates[:3], 1):
                print(f"  {i}. {candidate['disease']}: {candidate['confidence']:.1f}%")

        # Nếu có bệnh được chẩn đoán, lấy thêm explanation
        if diagnosed_disease:
            explanation = scorer.explain_diagnosis(diagnosed_disease, facts)
            print(f"[SMART DIAGNOSIS] Explanation for {diagnosed_disease}:")
            print(
                f"  - Matched positive symptoms: {len(explanation.get('matched_positive', []))}"
            )
            print(
                f"  - Matched negative symptoms: {len(explanation.get('matched_negative', []))}"
            )
            print(
                f"  - Missing important symptoms: {len(explanation.get('missing_important', []))}"
            )

        # Xử lý trường hợp KHÔNG chẩn đoán được bệnh cụ thể
        if not diagnosed_disease:
            print(
                "[DEBUG] No specific disease diagnosed - generating suggestions based on symptoms"
            )

            # Phân tích triệu chứng để đưa ra gợi ý
            symptom_analysis = _analyze_symptoms_without_diagnosis(
                facts, result.final_facts
            )

            diagnosed_disease = "unknown"
            disease_label = "Chưa đủ thông tin để chẩn đoán"
            disease_severity_raw = "Unknown"
            confidence = 0.0

            # Tạo recommendation dựa trên triệu chứng
            recommendation = kb.get_recommendation(diagnosed_disease)
            if not recommendation:
                recommendation = _generate_symptom_based_recommendation(
                    facts, result.final_facts, symptom_analysis
                )
        else:
            # Get recommendation cho bệnh đã chẩn đoán
            recommendation = kb.get_recommendation(diagnosed_disease)

        # === Chuẩn bị TOP DIAGNOSES (2-3 chẩn đoán khả năng cao nhất) ===
        top_diagnoses = []

        # Lọc các candidates có confidence >= 10% để hiển thị
        significant_candidates = [
            c for c in disease_candidates if c["confidence"] >= 10.0
        ]

        # Lấy top 3 (hoặc ít hơn nếu không đủ)
        for i, candidate in enumerate(significant_candidates[:3]):
            disease_code = candidate["disease"]
            disease_confidence = candidate["confidence"]

            # Get disease info
            disease_info = kb.get_disease_info(disease_code)

            if disease_info:
                disease_label_item = disease_info["label"]
                severity_raw_item = disease_info["severity"]
            else:
                disease_label_item = disease_code.replace("_", " ").title()
                severity_raw_item = "Unknown"

            # Map severity
            severity_map = {
                "Mild": "low",
                "Moderate": "medium",
                "Severe": "high",
                "Unknown": "low",
            }
            severity_item = severity_map.get(severity_raw_item, "low")

            # Translate severity to Vietnamese
            severity_vietnamese = {
                "Mild": "Nhẹ",
                "Moderate": "Trung bình",
                "Severe": "Nặng",
                "Unknown": "Không rõ",
            }
            severity_raw_vi = severity_vietnamese.get(severity_raw_item, "Không rõ")

            top_diagnoses.append(
                {
                    "rank": i + 1,
                    "disease": disease_code,
                    "disease_label": disease_label_item,
                    "confidence": disease_confidence,
                    "severity": severity_item,
                    "severity_raw": severity_raw_vi,
                    "is_primary": (i == 0),  # Primary diagnosis (highest confidence)
                }
            )

        print(f"[SMART DIAGNOSIS] Sending {len(top_diagnoses)} diagnoses to frontend")

        # Get primary diagnosis info (for backward compatibility)
        disease_info = (
            kb.get_disease_info(diagnosed_disease)
            if diagnosed_disease and diagnosed_disease != "unknown"
            else None
        )

        if not disease_info and diagnosed_disease != "unknown":
            disease_label = "Không xác định"
            disease_severity_raw = "Unknown"
        elif disease_info:
            disease_label = disease_info["label"]
            disease_severity_raw = disease_info["severity"]

        # Map severity to lowercase for CSS classes
        severity_map = {
            "Mild": "low",
            "Moderate": "medium",
            "Severe": "high",
            "Unknown": "low",
        }
        disease_severity = severity_map.get(disease_severity_raw, "low")

        # Translate severity to Vietnamese
        severity_vietnamese = {
            "Mild": "Nhẹ",
            "Moderate": "Trung bình",
            "Severe": "Nặng",
            "Unknown": "Không rõ",
        }
        disease_severity_raw_vi = severity_vietnamese.get(
            disease_severity_raw, "Không rõ"
        )

        # Build response
        response = {
            "ok": True,
            "session_id": session_id,
            "diagnosis": {
                "disease": diagnosed_disease,
                "disease_label": disease_label,
                "severity": disease_severity,
                "severity_raw": disease_severity_raw_vi,
                "confidence": confidence,
                "success": result.success,
            },
            "top_diagnoses": top_diagnoses,  # NEW: Top 2-3 chẩn đoán
            "symptoms": {
                "input": form_data,
                "extracted_facts": list(facts),
                "matched": (
                    [f for f in facts if f in result.final_facts]
                    if result.final_facts
                    else []
                ),
            },
            "recommendation": recommendation,
            "inference": {
                "fired_rules": result.fired_rules,
                "final_facts": result.final_facts,
                "steps": len(result.history),
            },
            "graphs": {
                "fpg": (
                    url_for(
                        "static", filename=f"generated/{session_id}/forward_fpg.svg"
                    )
                    if hasattr(result, "graph_files")
                    and result.graph_files
                    and "fpg" in result.graph_files
                    else None
                ),
                "rpg": (
                    url_for(
                        "static", filename=f"generated/{session_id}/forward_rpg.svg"
                    )
                    if hasattr(result, "graph_files")
                    and result.graph_files
                    and "rpg" in result.graph_files
                    else None
                ),
            },
        }

        # Save result for later retrieval
        _save_result(session_id, response)

        return jsonify(response)

    except Exception as e:
        return jsonify({"ok": False, "error": f"Inference error: {e}"}), 500


@medical_bp.get("/results/<session_id>")
def results(session_id: str):
    """Display diagnosis results."""
    # Load saved result
    result_data = _load_result(session_id)

    if not result_data:
        return render_template("error.html", error="Result not found or expired"), 404

    # Get KB for symptom labels
    try:
        kb = get_medical_kb()
    except Exception:
        kb = None

    # Extract data for template
    diagnosis = result_data.get("diagnosis", {})
    symptoms = result_data.get("symptoms", {})
    matched_symptoms_raw = symptoms.get("matched", [])

    # Convert symptom variables to human-readable labels
    matched_symptoms = []
    if kb:
        for symptom in matched_symptoms_raw:
            label = kb.get_symptom_label(symptom)
            matched_symptoms.append(label)
    else:
        matched_symptoms = matched_symptoms_raw

    recommendation = result_data.get("recommendation", "")

    # Parse recommendation into list if it's a string
    recommendations = []
    if recommendation:
        if isinstance(recommendation, list):
            recommendations = recommendation
        elif isinstance(recommendation, str):
            # Split by newlines or bullet points
            lines = recommendation.split("\n")
            recommendations = [
                line.strip("- •").strip() for line in lines if line.strip()
            ]

    # Get graphs
    graphs = result_data.get("graphs", {})
    fpg_image = graphs.get("fpg")
    rpg_image = graphs.get("rpg")

    # Get top diagnoses
    top_diagnoses = result_data.get("top_diagnoses", [])

    return render_template(
        "medical/results.html",
        diagnosis=diagnosis,
        top_diagnoses=top_diagnoses,  # NEW: Pass top diagnoses
        matched_symptoms=matched_symptoms,
        recommendations=recommendations,
        fpg_image=fpg_image,
        rpg_image=rpg_image,
        session_id=session_id,
        current_year=datetime.now().year,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _simple_extract_facts(form_data: Dict[str, Any]) -> Set[str]:
    """Simple fact extraction fallback."""
    facts = set()

    def is_true(value):
        """Helper to check if a value should be treated as True."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() not in ("false", "no", "0", "", "none")
        return bool(value)

    # Temperature
    nhiet_do = form_data.get("nhiet_do")
    if nhiet_do:
        try:
            nhiet_do = float(nhiet_do)
            if nhiet_do > 38:
                facts.add("sot")
            if nhiet_do > 38.5:
                facts.add("sot_cao")
        except (ValueError, TypeError):
            pass

    # Boolean symptoms
    if is_true(form_data.get("ho")):
        facts.add("ho")
        loai_ho = form_data.get("loai_ho")
        if loai_ho == "khan":
            facts.add("ho_khan")
        elif loai_ho == "co_dam":
            facts.add("ho_co_dam")

    if is_true(form_data.get("dau_dau")):
        facts.add("dau_dau")
    if is_true(form_data.get("met_moi")):
        facts.add("met_moi")
    if is_true(form_data.get("dau_hong")):
        facts.add("dau_hong")
    if is_true(form_data.get("chay_mui")):
        facts.add("chay_mui")
    if is_true(form_data.get("mat_vi_giac")):
        facts.add("mat_vi_giac")
    if is_true(form_data.get("mat_khu_giac")):
        facts.add("mat_khu_giac")
    if is_true(form_data.get("dau_nguc")):
        facts.add("dau_nguc")
    if is_true(form_data.get("kho_tho")):
        facts.add("kho_tho")
    if is_true(form_data.get("dau_bung")):
        facts.add("dau_bung")
    if is_true(form_data.get("buon_non")):
        facts.add("buon_non")
    if is_true(form_data.get("tieu_chay")):
        facts.add("tieu_chay")

    # SpO2
    spo2 = form_data.get("spo2")
    if spo2:
        try:
            spo2 = float(spo2)
            if spo2 < 95:
                facts.add("spo2_thap")
            else:
                facts.add("spo2_binh_thuong")
        except (ValueError, TypeError):
            pass

    # Age groups
    tuoi = form_data.get("tuoi")
    if tuoi:
        try:
            tuoi = int(tuoi)
            if tuoi < 15:
                facts.add("tre_em")
            elif tuoi >= 60:
                facts.add("nguoi_gia")
        except (ValueError, TypeError):
            pass

    return facts


def _get_possible_diseases(kb: Any) -> List[str]:
    """Get list of possible diseases as inference goals."""
    diseases = [
        "cam_thuong",
        "nghi_covid",
        "covid_19",
        "covid_nhe",
        "covid_nang",
        "viem_phoi",
        "hen_suyen",
        "viem_hong",
        "viem_da_day",
        "ngo_doc_thuc_pham",
    ]
    return diseases


def _save_result(session_id: str, result_data: Dict[str, Any]) -> None:
    """Save result to file for later retrieval."""
    output_root = Path(
        current_app.config.get(
            "GRAPH_OUTPUT_ROOT", "inference_lab/web/static/generated"
        )
    )
    result_file = output_root / session_id / "result.json"

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)


def _load_result(session_id: str) -> Dict[str, Any] | None:
    """Load saved result from file."""
    output_root = Path(
        current_app.config.get(
            "GRAPH_OUTPUT_ROOT", "inference_lab/web/static/generated"
        )
    )
    result_file = output_root / session_id / "result.json"

    if not result_file.exists():
        return None

    with open(result_file, "r", encoding="utf-8") as f:
        return json.load(f)
