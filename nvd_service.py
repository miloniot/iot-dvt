import requests
import os
import time
from rapidfuzz import fuzz
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()

# The base URL for the NVD CVE API
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Get the API key from the .env file
NVD_API_KEY = os.getenv("NVD_API_KEY")


# This is the main function that searches for vulnerabilities
# It uses a multi-step hybrid approach:
# Step 1: Search with full name (e.g. "Xiaomi Mi Wi-Fi Router 3")
# Step 2: Search with just manufacturer (e.g. "Xiaomi")
# Step 3: Search with just model (e.g. "Mi Wi-Fi Router")
# Step 4: Combine all results and remove duplicates
# Step 5: Use fuzzy matching to rank results by relevance
def search_vulnerabilities(manufacturer, model):
    all_vulnerabilities = []
    seen_cve_ids = set()  # Used to avoid duplicates

    # Add the API key to the request headers
    headers = {
        "apiKey": NVD_API_KEY
    }

    # List of search queries to try — from most specific to least specific
    search_queries = [
        f"{manufacturer} {model}",  # Full name e.g. "Xiaomi Mi Wi-Fi Router 3"
        manufacturer,               # Just manufacturer e.g. "Xiaomi"
        model,                      # Just model e.g. "Mi Wi-Fi Router 3"
        # Try without numbers in model name
        ' '.join([w for w in model.split() if not w.isdigit()])
    ]

    # Remove empty or duplicate queries
    search_queries = list(dict.fromkeys([q.strip() for q in search_queries if q.strip()]))

    for query in search_queries:
        try:
            params = {
                "keywordSearch": query,
                "resultsPerPage": 10
            }

            # Send the request to the NVD API
            response = requests.get(
                NVD_API_URL,
                params=params,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get("vulnerabilities", [])

                for item in vulnerabilities:
                    cve = item.get("cve", {})
                    cve_id = cve.get("id", "Unknown")

                    # Skip if we already have this CVE
                    if cve_id in seen_cve_ids:
                        continue

                    seen_cve_ids.add(cve_id)

                    # Get the description
                    descriptions = cve.get("descriptions", [])
                    description = ""
                    for d in descriptions:
                        if d.get("lang") == "en":
                            description = d.get("value", "")
                            break

                    # Get severity
                    severity = get_severity(cve)

                    # Use fuzzy matching to check relevance
                    # We check against both manufacturer and model
                    keyword = f"{manufacturer} {model}".lower()
                    match_score = fuzz.partial_ratio(
                        keyword,
                        description.lower()
                    )

                    # Also check manufacturer and model separately
                    manufacturer_score = fuzz.partial_ratio(
                        manufacturer.lower(),
                        description.lower()
                    )
                    model_score = fuzz.partial_ratio(
                        model.lower(),
                        description.lower()
                    )

                    # Take the highest match score
                    best_score = max(match_score, manufacturer_score, model_score)

                    # Lower threshold to catch more results
                    if best_score >= 20:
                        all_vulnerabilities.append({
                            "cve_id": cve_id,
                            "description": description,
                            "severity": severity,
                            "plain_summary": make_plain_summary(description, severity),
                            "recommendation": get_recommendation(severity),
                            "match_score": best_score
                        })

            # Wait briefly between requests to respect NVD rate limits
            time.sleep(0.5)

        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            continue

    # Sort by severity first, then by match score
    all_vulnerabilities.sort(
        key=lambda x: (severity_order(x["severity"]), -x["match_score"])
    )

    # Return top 10 results to keep it manageable
    return all_vulnerabilities[:10]


# This function extracts the severity level from the CVE data
def get_severity(cve):
    try:
        metrics = cve.get("metrics", {})

        # Try CVSS v3.1 first
        if "cvssMetricV31" in metrics:
            return metrics["cvssMetricV31"][0]["cvssData"]["baseSeverity"]

        # Then try CVSS v3.0
        if "cvssMetricV30" in metrics:
            return metrics["cvssMetricV30"][0]["cvssData"]["baseSeverity"]

        # Then try CVSS v2
        if "cvssMetricV2" in metrics:
            score = metrics["cvssMetricV2"][0]["cvssData"]["baseScore"]
            if score >= 9.0:
                return "CRITICAL"
            elif score >= 7.0:
                return "HIGH"
            elif score >= 4.0:
                return "MEDIUM"
            else:
                return "LOW"
    except:
        pass

    return "UNKNOWN"


# This function converts a technical description
# into a simple plain English summary
def make_plain_summary(description, severity):
    if not description:
        return "A security vulnerability was found in this device."

    short = description[:100] + "..." if len(description) > 100 else description
    return f"This device may be at risk: {short}"


# This function gives a simple recommended action
# based on how severe the vulnerability is
def get_recommendation(severity):
    recommendations = {
        "CRITICAL": "Immediately disconnect this device and contact the manufacturer for a patch.",
        "HIGH": "Update the device firmware as soon as possible.",
        "MEDIUM": "Check for firmware updates and change default passwords.",
        "LOW": "Monitor the device and apply updates during your next maintenance window.",
        "UNKNOWN": "Check the manufacturer's website for any security updates."
    }
    return recommendations.get(severity, recommendations["UNKNOWN"])


# This function helps sort vulnerabilities
# so Critical ones appear first
def severity_order(severity):
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    return order.get(severity, 4)