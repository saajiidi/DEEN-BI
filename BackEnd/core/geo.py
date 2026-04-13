import re

# ISO 3166-2:BD District Mappings (Standard for WooCommerce BD)
BD_DISTRICTS = {
    "BD-01": "Bandarban",
    "BD-02": "Barguna",
    "BD-03": "Bogura",
    "BD-04": "Brahmanbaria",
    "BD-05": "Bagerhat",
    "BD-06": "Barishal",
    "BD-07": "Bhola",
    "BD-08": "Cumilla",
    "BD-09": "Chandpur",
    "BD-10": "Chattogram",
    "BD-11": "Cox's Bazar",
    "BD-12": "Chuadanga",
    "BD-13": "Dhaka",
    "BD-14": "Dinajpur",
    "BD-15": "Faridpur",
    "BD-16": "Feni",
    "BD-17": "Gopalganj",
    "BD-18": "Gazipur",
    "BD-19": "Gaibandha",
    "BD-20": "Habiganj",
    "BD-21": "Jamalpur",
    "BD-22": "Jashore",
    "BD-23": "Jhenaidah",
    "BD-24": "Joypurhat",
    "BD-25": "Jhalokathi",
    "BD-26": "Kishoreganj",
    "BD-27": "Khulna",
    "BD-28": "Kurigram",
    "BD-29": "Khagrachhari",
    "BD-30": "Kushtia",
    "BD-31": "Lakshmipur",
    "BD-32": "Lalmonirhat",
    "BD-33": "Manikganj",
    "BD-34": "Mymensingh",
    "BD-35": "Munshiganj",
    "BD-36": "Madaripur",
    "BD-37": "Magura",
    "BD-38": "Moulvibazar",
    "BD-39": "Meherpur",
    "BD-40": "Narayanganj",
    "BD-41": "Netrakona",
    "BD-42": "Narsingdi",
    "BD-43": "Narail",
    "BD-44": "Natore",
    "BD-45": "Chapai Nawabganj",
    "BD-46": "Nilphamari",
    "BD-47": "Noakhali",
    "BD-48": "Naogaon",
    "BD-49": "Pabna",
    "BD-50": "Pirojpur",
    "BD-51": "Patuakhali",
    "BD-52": "Panchagarh",
    "BD-53": "Rajbari",
    "BD-54": "Rajshahi",
    "BD-55": "Rangpur",
    "BD-56": "Rangamati",
    "BD-57": "Sherpur",
    "BD-58": "Satkhira",
    "BD-59": "Sirajganj",
    "BD-60": "Sylhet",
    "BD-61": "Sunamganj",
    "BD-62": "Shariatpur",
    "BD-63": "Tangail",
    "BD-64": "Thakurgaon"
}

# Key areas in Dhaka for sub-district refinement
DHAKA_AREAS = [
    "Uttara", "Gulshan", "Dhanmondi", "Banani", "Mirpur", "Mohammadpur", 
    "Motijheel", "Bashundhara", "Badda", "Rampura", "Jatrabari", "Farmgate",
    "Khilgaon", "Malibagh", "Moghbazar", "Tongi", "Savar", "Old Dhaka", "Keraniganj"
]

def clean_geo_name(input_str: str) -> str:
    """Removes ISO codes like BD-** and extra whitespace."""
    if not input_str: return "Unknown"
    # Remove BD-** codes
    clean = re.sub(r'BD-\d{2}', '', str(input_str), flags=re.IGNORECASE)
    # Remove commas and common artifacts
    clean = clean.replace(',', '').strip()
    return clean if clean else "Unknown"

def get_parent_district(district_code_or_name: str) -> str:
    """Returns the cleaned, standard parent district name for mapping."""
    if not district_code_or_name: return "Unknown"
    
    dist_str = str(district_code_or_name).strip().upper()
    
    # 1. Handle numeric strings or single codes (WooCommerce standard)
    # E.g., "13" -> "BD-13", "8" -> "BD-08"
    if dist_str.isdigit():
        dist_str = f"BD-{int(dist_str):02d}"
    elif len(dist_str) <= 2 and dist_str.isalnum():
        dist_str = f"BD-{dist_str.zfill(2)}"
        
    return BD_DISTRICTS.get(dist_str, clean_geo_name(dist_str))

def get_region_display(city: str, district: str) -> str:
    """
    Main logic for geographic intelligence.
    Converts ISO codes to names and refines Dhaka into specific areas.
    """
    city_str = str(city).strip() if city else ""
    dist_str = str(district).strip().upper() if district else ""
    
    # 1. Resolve District Name from Code
    district_name = get_parent_district(dist_str)
    
    # 2. Refinement Logic for Dhaka
    if district_name.lower() == "dhaka":
        # Check if city/area name is prominent
        for area in DHAKA_AREAS:
            if area.lower() in city_str.lower():
                return f"{area}, Dhaka"
        # If city contains useful info, use it, else just Dhaka
        if city_str and city_str.lower() != "dhaka":
            return f"{city_str.title()}, Dhaka"
        return "Dhaka City"
    
    # 3. Standard formatting (City, District) if they differ
    if city_str and city_str.lower() != district_name.lower():
        clean_city = clean_geo_name(city_str).title()
        if clean_city != "Unknown" and clean_city.lower() != district_name.lower():
            # If city is already in district_name, don't repeat
            if clean_city.lower() in district_name.lower():
                return district_name
            return f"{clean_city}, {district_name}"
            
    return district_name
