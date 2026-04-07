import pandas as pd

def apply_filters(orders, products, filters):
    """
    Apply all 7 clusters of filters to the orders data.
    """
    if not orders:
        return pd.DataFrame()

    # Flatten orders to item level for deep filtering
    flat_data = []
    for order in orders:
        order_id = order.get("id")
        created_at = order.get("date_created")
        status = order.get("status")
        total = float(order.get("total", 0))
        coupon_lines = order.get("coupon_lines", [])
        coupons = [c.get("code") for c in coupon_lines]
        
        # Metadata extraction
        meta = {m['key']: m['value'] for m in order.get("meta_data", [])}
        platform = meta.get("platform", "E-commerce") # Default
        location = meta.get("location", "Online")

        items = order.get("line_items", [])
        is_bundle = len(items) > 1

        for item in items:
            item_meta = {m['key']: m['value'] for m in item.get("meta_data", [])}
            
            flat_data.append({
                "order_id": order_id,
                "date": created_at,
                "status": status,
                "order_total": total,
                "product_id": item.get("product_id"),
                "sku": item.get("sku"),
                "product_name": item.get("name"),
                "quantity": item.get("quantity"),
                "price": float(item.get("price", 0)),
                "item_total": float(item.get("total", 0)),
                "color": item_meta.get("pa_color", item_meta.get("Color", "N/A")),
                "size": item_meta.get("pa_size", item_meta.get("Size", "N/A")),
                "fit": item_meta.get("pa_fit", item_meta.get("Fit", "N/A")),
                "platform": platform,
                "location": location,
                "coupons": coupons,
                "is_bundle": is_bundle
            })

    df = pd.DataFrame(flat_data)
    if df.empty:
        return df

    # 1. Product (Category, SKU)
    # Categories are not in order items, need mapping from products
    if filters.get("categories") or filters.get("skus"):
        prod_map = {p['id']: [c['name'] for c in p.get('categories', [])] for p in products}
        df['categories'] = df['product_id'].map(prod_map)
        
        if filters.get("categories"):
            df = df[df['categories'].apply(lambda x: any(c in filters['categories'] for c in x) if isinstance(x, list) else False)]
        
        if filters.get("skus"):
            df = df[df['sku'].isin(filters['skus'])]

    # 2. Variant Filter (Color, Size, Fit)
    if filters.get("colors"):
        df = df[df['color'].isin(filters['colors'])]
    if filters.get("sizes"):
        df = df[df['size'].isin(filters['sizes'])]
    if filters.get("fits"):
        df = df[df['fit'].isin(filters['fits'])]

    # 3. Price Based Filter
    min_p, max_p = filters.get("price_range", (0, 100000))
    df = df[(df['price'] >= min_p) & (df['price'] <= max_p)]

    # 4. Location/Platform Based Filter
    if filters.get("platforms"):
        df = df[df['platform'].isin(filters['platforms'])]

    # 5. Campaign Based Filter (Campaign Category, Coupon, Bundle)
    if filters.get("coupons"):
        df = df[df['coupons'].apply(lambda x: any(c in filters['coupons'] for c in x))]
    
    if filters.get("is_bundle") is not None:
        df = df[df['is_bundle'] == filters['is_bundle']]

    return df
