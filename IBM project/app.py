import json, re
from flask import Flask, request, jsonify, render_template
from agents import profile_agent, eligibility_agent, discovery_agent
from agents import proposal_agent, compliance_agent, review_agent


app = Flask(__name__)


def repair_json(text):
    """
    Attempt to repair a truncated JSON string from the model.
    Tries direct parse first, then strips markdown fences,
    then attempts to close any unclosed arrays/objects.
    """
    if not text:
        return None
    s = text.strip()
    # Strip markdown fences
    if s.startswith("```"):
        s = s.split("\n", 1)[-1]
        s = re.sub(r"```\s*$", "", s).strip()
    # Try direct parse
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Find the first { or [
    m = re.search(r"[\[{]", s)
    if not m:
        return None
    s = s[m.start():]
    # Remove any trailing incomplete item: cut at last complete comma-separated entry
    # by finding last }, or ], and closing the structure
    for cutpoint in range(len(s) - 1, -1, -1):
        ch = s[cutpoint]
        if ch in ('}', ']'):
            candidate = s[:cutpoint + 1]
            # Count open brackets and close them
            opens = candidate.count('[') - candidate.count(']')
            opens_b = candidate.count('{') - candidate.count('}')
            candidate += ']' * opens + '}' * opens_b
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    user_input = request.json.get("description")

    profile = profile_agent.run(user_input)
    eligibility = eligibility_agent.run(profile)

    # Use repair_json to handle truncated responses from the model
    eligibility_parsed = repair_json(eligibility)
    if isinstance(eligibility_parsed, dict):
        matched_schemes = eligibility_parsed.get("eligible", [])
        # Send back repaired JSON so frontend always gets valid data
        eligibility_out = json.dumps(eligibility_parsed)
    else:
        matched_schemes = []
        eligibility_out = eligibility  # send raw, frontend will show fallback

    discovery = discovery_agent.run(matched_schemes)

    return jsonify({
        "profile": profile,
        "eligibility": eligibility_out,
        "discovery": discovery
    })

@app.route("/api/generate-proposal", methods=["POST"])
def generate_proposal():
    profile = request.json.get("profile")
    scheme = request.json.get("scheme")

    proposal = proposal_agent.run(profile, scheme)
    compliance = compliance_agent.run(scheme)
    review = review_agent.run(proposal)

    return jsonify({
        "proposal": proposal,
        
        "compliance": compliance,
        "review": review
    })

@app.route("/api/guided-build", methods=["POST"])
def guided_build():
    """Assembles a natural-language description from structured guided-form fields."""
    d = request.json or {}
    name        = d.get("startup_name", "").strip()
    sector      = d.get("sector", "").strip()
    subsector   = d.get("subsector", "").strip()
    stage       = d.get("stage", "").strip()
    city        = d.get("city", "").strip()
    state_      = d.get("state", "").strip()
    funding_pref = d.get("dpiit_registered", "Either")  # field repurposed as funding type preference
    founding    = d.get("founding_year", "").strip()
    team_size   = d.get("team_size", "").strip()
    problem     = d.get("problem_statement", "").strip()
    solution    = d.get("solution", "").strip()
    revenue     = d.get("revenue_model", "").strip()
    funding_amt = d.get("funding_amount", "").strip()
    funding_use = d.get("funding_use", "").strip()
    ip          = d.get("ip_status", "").strip()
    target      = d.get("target_beneficiary", "").strip()

    parts = []
    if name:
        parts.append(f"Startup name: {name}.")
    if sector:
        full_sector = f"{sector}" + (f" ({subsector})" if subsector else "")
        parts.append(f"We operate in the {full_sector} sector.")
    if stage:
        parts.append(f"Current stage: {stage}.")
    if city or state_:
        loc = ", ".join(filter(None, [city, state_]))
        parts.append(f"Location: {loc}.")
    if funding_pref and funding_pref != "Either":
        parts.append(f"Funding type preference: {funding_pref}.")
    if founding:
        parts.append(f"Founded in {founding}.")
    if team_size:
        parts.append(f"Team size: {team_size} people.")
    if problem:
        parts.append(f"Problem we solve: {problem}.")
    if solution:
        parts.append(f"Our solution: {solution}.")
    if revenue:
        parts.append(f"Revenue model: {revenue}.")
    if target:
        parts.append(f"Target beneficiaries: {target}.")
    if ip:
        parts.append(f"IP status: {ip}.")
    if funding_amt:
        parts.append(f"We are seeking {funding_amt} in grant funding.")
    if funding_use:
        parts.append(f"Funds will be used for: {funding_use}.")

    description = " ".join(parts) if parts else "Startup seeking government grant funding."
    return jsonify({"description": description})


if __name__ == "__main__":
    app.run(debug=True)