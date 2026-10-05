import httpx

def test_overpass():
    query = """
    [out:json][timeout:15];
    (
      node["amenity"="cafe"](28.40,77.29,28.63,77.50);
      node["amenity"="restaurant"](28.40,77.29,28.63,77.50);
      node["amenity"="dentist"](28.40,77.29,28.63,77.50);
    );
    out tags 20;
    """
    resp = httpx.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=15.0)
    print("Status:", resp.status_code)
    data = resp.json()
    elements = data.get("elements", [])
    print(f"Found {len(elements)} elements")
    for el in elements[:8]:
        tags = el.get("tags", {})
        name = tags.get("name")
        if name:
            print(f"- Name: {name}, Amenity: {tags.get('amenity')}, Website: {tags.get('website') or tags.get('contact:website')}, Phone: {tags.get('phone') or tags.get('contact:phone')}")

if __name__ == "__main__":
    test_overpass()
