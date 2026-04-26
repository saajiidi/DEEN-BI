import pandas as pd

CATEGORY_MAPPING = {
    'Boxer': ['boxer'],
    'T-Shirt - Tank Top': ['tank top', 'tanktop', 'tank', 'top'],
    'Jeans': ['jeans'],
    'FS Shirt - Denim Shirt': ['denim'],
    'FS Shirt - Flannel Shirt': ['flannel'],
    'FS Shirt - Oxford Shirt': ['oxford'],
    'FS Shirt - Executive Formal Shirt': ['executive', 'formal'],
    'Polo Shirt': ['polo'],
    'Panjabi': ['panjabi', 'punjabi'],
    'Trousers': ['trousers', 'pant', 'cargo', 'trouser', 'joggers', 'track pant', 'jogger'],
    'Twill Chino': ['twill chino'],
    'Mask': ['mask'],
    'Water Bottle': ['water bottle'],
    'HS Shirt - Contrast Shirt': ['contrast'],
    'Turtleneck': ['turtleneck', 'mock neck'],
    'T-Shirt - Drop Shoulder': ['drop shoulder'],
    'Wallet': ['wallet'],
    'FS Shirt - Kaftan Shirt': ['kaftan'],
    'T-Shirt - Active Wear': ['active wear', 'activewear'],
    'T-Shirt - Jersey': ['jersy', 'jersey'],
    'Sweatshirt': ['sweatshirt', 'hoodie', 'pullover'],
    'Jacket': ['jacket', 'outerwear', 'coat'],
    'Belt': ['belt'],
    'Sweater': ['sweater', 'cardigan', 'knitwear'],
    'Passport Holder': ['passport holder'],
    'Cap': ['cap'],
    'Leather Bag': ['bag', 'backpack'],
}

def get_product_category(name: str) -> str:
    """Expert rule-based categorization for DEEN products."""
    if not name or not isinstance(name, str):
        return "Others"
        
    name_str = name.lower()
    for cat, keywords in CATEGORY_MAPPING.items():
        if any(kw.lower() in name_str for kw in keywords):
            if cat == 'Jeans':
                if any(kw in name_str for kw in ['slim']):
                    return "Jeans - Slim Fit"
                if any(kw in name_str for kw in ['regular']):
                    return "Jeans - Regular Fit"
                if any(kw in name_str for kw in ['straight']):
                    return "Jeans - Straight Fit"
            return cat
    
    # Special handling for T-Shirts and Shirts (Sleeve Logic)
    fs_keywords = ['full sleeve', 'long sleeve', 'fs', 'l/s']
    is_fs = any(kw in name_str for kw in fs_keywords)
    
    if any(kw in name_str for kw in ['t-shirt', 't shirt', 'tee']):
        return 'T-Shirt - FS T-Shirt' if is_fs else 'T-Shirt - HS T-Shirt'
    if 'shirt' in name_str:
        return 'FS Shirt' if is_fs else 'HS Shirt - HS Casual Shirt'
        
    return 'Others'

def apply_category_expert_rules(df: pd.DataFrame, name_col: str = "item_name") -> pd.DataFrame:
    """Applies the mapping to a dataframe and adds a 'Category' column."""
    if df.empty or name_col not in df.columns:
        return df
    df['Category'] = df[name_col].apply(get_product_category)
    return df
