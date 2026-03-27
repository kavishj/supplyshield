import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from config import GATE_APPROVAL_THRESHOLD

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gate")

app = FastAPI(title="ProcurementGateAgent", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class GateRequest(BaseModel):
    company_name:           str
    risk_score:             float
    risk_category:          str
    ofac_status:            str
    ofac_50_rule_triggered: bool = False
    ofac_50_rule_pct:       float = 0.0


@app.get("/health")
def health():
    return {
        "agent":     "ProcurementGateAgent",
        "status":    "healthy",
        "threshold": GATE_APPROVAL_THRESHOLD,
        "version":   "3.0.0",
    }


@app.post("/evaluate")
def evaluate(req: GateRequest):
    start = time.perf_counter()

    if req.ofac_status == "SANCTIONED":
        decision = "BLOCKED"
        reason   = f"{req.company_name} matched OFAC SDN sanctions list. Procurement halted."
        action   = "Escalate to legal team immediately. Do not place any orders."
    elif req.ofac_50_rule_triggered:
        decision = "BLOCKED"
        reason   = (
            f"{req.company_name} blocked under OFAC 50% Rule — OFAC-listed parties "
            f"cumulatively hold {req.ofac_50_rule_pct:.1f}% of this company."
        )
        action   = "Escalate to legal and compliance team. Do not place any orders."
    elif req.risk_score >= GATE_APPROVAL_THRESHOLD:
        decision = "REQUIRES_APPROVAL"
        reason   = f"Risk score {req.risk_score:.3f} exceeds approval threshold {GATE_APPROVAL_THRESHOLD}."
        action   = "Route to procurement manager for manual review before proceeding."
    else:
        decision = "AUTO_APPROVED"
        reason   = f"Risk score {req.risk_score:.3f} is within acceptable limits (threshold: {GATE_APPROVAL_THRESHOLD})."
        action   = "Proceed with standard supplier onboarding process."

    elapsed = round((time.perf_counter() - start) * 1000, 2)
    logger.info(f"Gate decision for '{req.company_name}': {decision} in {elapsed}ms")

    return {
        "decision":   decision,
        "reason":     reason,
        "action":     action,
        "threshold":  GATE_APPROVAL_THRESHOLD,
        "elapsed_ms": elapsed,
    }
