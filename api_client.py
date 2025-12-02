# api_client.py - RFID to Article mapping

rfid_to_article_mapping = {
    "0386561177942": "Premium Coffee Beans",
    "0210462015227": "Premium Coffee Beans",  # Same article, different tag
    "0386561177942": "Organic Green Tea",
    "0210462016561": "Organic Green Tea",     # Same article, different tag
    "0386561199531": "Hot Chocolategit",
    "0004859272": "Fresh Orange Juice",
    "0004859273": "Whole Wheat Bread",
}

def fetch_article(rfid_tag: str) -> str:
    """
    Takes RFID tag as string, returns article name as string.
    Returns None if tag not found.
    """
    article = rfid_to_article_mapping.get(rfid_tag.strip())
    if article:
        print(f"✓ Found: {rfid_tag} → {article}")
        return article
    print(f"✗ Unknown tag: {rfid_tag}")
    return None
