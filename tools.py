import pandas as pd
from datetime import datetime

products = pd.read_csv("products.csv")
orders = pd.read_csv("orders.csv")

# with open("policy.txt") as f:
#     policy = f.read()

def parse_stock(stock_str):
    """
    stock_per_size stored like:
    "{'6': 5, '8': 0, '10': 3}"
    """
    try:
        return eval(stock_str)
    except:
        return {}

def search_products(**filters):
    
    df = products.copy()
        
    if "max_price" in filters:
        df = df[df["price"] <= filters["max_price"]]

    if "size" in filters:
        size = str(filters["size"])
        df = df[df["sizes_available"].astype(str).str.contains(size)]

        df = df[
            df["stock_per_size"].apply(
                lambda x: parse_stock(x).get(size, 0) > 0
            )
        ]

    
    if filters.get("on_sale") or filters.get("clearance"):
        mask = False

        if filters.get("on_sale"):
            mask = mask | (df["is_sale"] == True)

        if filters.get("clearance"):
            mask = mask | (df["is_clearance"] == True)

        df = df[mask]
    
        
    if "tags" in filters:
        tags = [tag for x in filters["tags"] for tag in x.split()]
        mask = df["tags"].str.contains("|".join(tags), case=False, na=False)
        df = df[mask]
        
    if "vendors" in filters:
        vendors = [vendor for x in filters["vendors"] for vendor in x.split()]
        vendors_lower = [v.lower() for v in vendors]
        pattern = "|".join(vendors_lower)
        mask = df["vendor"].fillna("").str.lower().str.contains(pattern, na=False)
        df = df[mask]
    
    df = df.sort_values(by="bestseller_score", ascending=False)

    return df.head(filters["number_of_products"]).to_dict(orient="records") if "number_of_products" in filters else df.head(5).to_dict(orient="records")


def get_product(product_id):
    row = products[products["product_id"] == product_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def get_order(order_id):
    
    row = orders[orders["order_id"] == order_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def evaluate_return(order_id):
    order = get_order(order_id)
    if not order:
        return {"error": "Order not found"}

    product = get_product(order["product_id"])
    if not product:
        return {"error": "Product not found"}

    order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
    days_since = (datetime.now() - order_date).days
    vendor = product.get("vendor", "")
    sale = product.get("is_sale", False)
    clearance = product.get("is_clearance", False)

    
    if vendor == "Aurelia Couture":
        return {
            "eligible": True,
            "type": "exchange_only",
            "reason": "Vendor policy: exchanges only, no refunds"
        }
        
    if vendor == "Nocturne":
        if days_since <= 21:
            return {
                "eligible": True,
                "type": "refund",
                "reason": "Vendor policy: 21-day return window"
            }
        else:
            return {
                "eligible": False,
                "type": "none",
                "reason": "Exceeded 21-day vendor return window"
            }
    if clearance:
        return {
            "eligible": False,
            "type": "none",
            "reason": "Clearance item: final sale, not eligible for return or exchange"
        }

    

    if sale:
        if days_since <= 7:
            return {
                "eligible": True,
                "type": "store_credit",
                "reason": "Sale item: eligible within 7 days for store credit"
            }
        else:
            return {
                "eligible": False,
                "type": "none",
                "reason": "Sale return window (7 days) expired"
            }

    if days_since <= 14:
        return {
            "eligible": True,
            "type": "refund",
            "reason": "Within 14-day return window"
        }
    else:
        return {
            "eligible": False,
            "type": "none",
            "reason": "Return window expired"
        }


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search products with filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_price": {"type": "number"},
                    "size": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "on_sale": {"type": "boolean"},
                    "clearance": {"type": "boolean"},
                    "vendors": {"type": "array", "items": {"type": "string"}},
                    "number_of_products": {"type": "number"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string"},
                    
                },
                
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_return",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"}
                },
                "required": ["order_id"]
            }
        }
    }
]

tool_map = {
    "search_products": search_products,
    "get_product": get_product,
    "get_order": get_order,
    "evaluate_return": evaluate_return
}