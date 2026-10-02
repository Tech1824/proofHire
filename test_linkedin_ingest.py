from ingest.linkedin import extract_linkedin_claims

def test_extract():
    text = """
    I am a cybersecurity student and OSINT enthusiast who loves the mechanics of hacking.
    I spend my free time diving into cybercrime investigation, digital forensics, and AI Red Teaming.
    I built a Python script using BeautifulSoup and Pandas to scrape dark web forums.
    My goal is to keep improving my technical skills so I can ethically support digital investigations.
    """
    print("Extracting claims from LinkedIn text...")
    res = extract_linkedin_claims(text)
    print(res)

if __name__ == "__main__":
    test_extract()
