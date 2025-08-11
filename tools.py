from langchain.tools import tool
import re

@tool
def parse_claim_text(text: str) -> list:
    """
    Parses claim data from raw text and returns structured information.
    """
    claims = []
    claim_blocks = text.split("Claim Number:")[1:]

    for block in claim_blocks:
        claim = {}
        lines = block.strip().splitlines()

        # Basic structure parsing
        claim_number_line = lines[0].strip()
        claim["Claim Number"] = claim_number_line.split()[0]

        # Extract Dates
        for line in lines:
            if "Accident Date" in line and "Notice Date" in line and "Close Date" in line:
                parts = re.findall(r'\d{2}/\d{2}/\d{4}', line)
                if len(parts) == 3:
                    claim["Accident Date"] = parts[0]
                    claim["Notice Date"] = parts[1]
                    claim["Close Date"] = parts[2]

        # Incident description
        description = []
        for line in lines:
            if any(keyword in line.lower() for keyword in ["accident", "stole", "flood", "damage", "collision"]):
                description.append(line.strip())
        claim["Incident Description"] = " ".join(description)

        claims.append(claim)

    return claims
